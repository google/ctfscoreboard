import flask
import functools
import json

from app import app
import models
import csrfutil


class ValidationError(Exception):
  pass


@app.before_request
def load_globals():
  uid = flask.session.get('user')
  if uid:
    user = models.User.query.get(uid)
    if user:
      flask.g.user = user
      flask.g.team = user.team
      return
  flask.g.user = None
  flask.g.team = None


def login_required(f):
  @functools.wraps(f)
  def wrapper(*args, **kwargs):
    if not flask.g.user:
      flask.flash('You must be logged in.', 'danger')
      return flask.redirect(flask.url_for('login'))
    return f(*args, **kwargs)
  return wrapper


def admin_required(f):
  @functools.wraps(f)
  def wrapper(*args, **kwargs):
    try:
      if not flask.g.user.admin:
        abort(403)
    except AttributeError:
      abort(403)
    return f(*args, **kwargs)
  return wrapper


@app.route('/')
def index():
  return flask.render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
@csrfutil.csrf_protect
def login():
  if flask.request.method == 'POST':
    email = flask.request.form.get('email')
    password = flask.request.form.get('password')
    if email and password:
      user = models.User.login_user(email, password)
      if user:
        flask.session['user'] = user.uid
        return flask.redirect(flask.url_for('challenges'))
    flask.flash('Invalid username/password.')
  return flask.render_template('login.html')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
  flask.session['user'] = None
  flask.flash('You have successfully logged out.', 'success')
  return flask.redirect(flask.url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
  if flask.request.method == 'POST':
    try:
      email = flask.request.form.get('email')
      nick = flask.request.form.get('nick')
      password = flask.request.form.get('password')
      for fname, field in (('email', 'Email'), ('nick', 'Handle'),
          ('password', 'Password'), ('password2', 'Repeat Password')):
        if not flask.request.form.get(fname):
          raise ValidationError('%s is a required field.' % field)
      if password != flask.request.form.get('password2'):
        raise ValidationError('Passwords do not match.')
      # TODO: validate email
      if app.config.get("TEAMS"):
        team = flask.request.form.get('team')
        if team == 'new':
          team = models.Team.create(flask.request.form.get('team-name'))
        else:
          team = models.Team.query.get(int(team))
          if not team or (flask.request.form.get('team-code', '').lower()
              != team.code.lower()):
            raise ValidationError('Invalid team selection or team code.')
      else:
        team = None
      user = models.User.create(email, nick, password, team=team)
      flask.session['user'] = user.uid
      flask.flash('Registration successful.', 'success')
      return flask.redirect(flask.url_for('challenges'))
    except ValidationError as ex:
      flask.flash(str(ex), 'danger')
  return flask.render_template('register.html',
      teams=models.Team.query.all())


def _enumerate_teams():
  return enumerate(models.Team.query.order_by(
    models.Team.score.desc()).all(), 1)


@app.route('/scoreboard')
def scoreboard():
  return flask.render_template('scoreboard.html',
      teams=_enumerate_teams())


@app.route('/scoreboard.json')
def scoreboard_json():
  scores = []
  for pos, team in _enumerate_teams():
    scores.append({
      'place': pos,
      'team': team.name,
      'score': team.score
      })
  return flask.jsonify(scores=scores)


@app.route('/challenges')
@login_required
def challenges():
  return flask.render_template('challenges.html',
      categories=models.Category.query.all())


@app.route('/challenges/<int:cat>')
@login_required
def challenges_by_cat(cat):
  categories = models.Category.query.all()
  cfilter = [c for c in categories if c.cid==cat]
  if not cfilter:
    flask.flash('No such category.', 'warning')
    return flask.redirect(flask.url_for('challenges'))
  category = cfilter[0]
  if not category.unlocked:
    flask.flash('Category is locked.', 'warning')
    return flask.redirect(flask.url_for('challenges'))
  return flask.render_template('challenges.html',
      categories=categories,
      category=category,
      challenges=models.Challenge.query.filter(
        models.Challenge.cid == cat,
        models.Challenge.unlocked == True).all())


@app.route('/submit/<int:cid>', methods=['POST'])
@login_required
@csrfutil.csrf_protect
def submit(cid):
  challenge = models.Challenge.query.get(cid)
  answer = flask.request.form.get('answer')
  if challenge.verify_answer(answer):
    flask.g.team.score += challenge.points
    models.Answer.create(challenge, flask.g.team, answer)
    flask.flash('Congratulations!  %d points awarded.' % challenge.points,
        'success')
  else:
    flask.flash('Really?  Haha no...', 'warning')
  return flask.redirect(flask.url_for(
    'challenges_by_cat', cat=challenge.cat_cid))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
@csrfutil.csrf_protect
def profile():
  if flask.request.method == 'POST':
    # TODO: more change types
    dirty = False
    pw = flask.request.form.get('password')
    pw2 = flask.request.form.get('password2')
    if pw and pw == pw2:
      flask.g.user.set_password(pw)
      dirty = True
      flask.flash('Password updated.', 'success')
    if dirty:
      models.commit()
    return flask.redirect(flask.url_for(flask.request.endpoint))
  return flask.render_template('profile.html')


# Admin UI
@app.route('/admin/makemeadmin')
@login_required
def makemeadmin():
  # Only works if no other admins exist
  if models.User.query.filter(models.User.admin == True).count():
    flask.abort(403)
  flask.g.user.admin = True
  models.commit()
  return flask.redirect(flask.url_for('index'))


@app.route('/admin/categories', methods=['GET', 'POST'])
@login_required
@admin_required
@csrfutil.csrf_protect
def admin_categories():
  if flask.request.method == 'POST':
    def getcid():
      try:
        return int(flask.request.form.get('cid'))
      except TypeError:
        raise ValidationError('Invalid category id.')
    def getcat():
      cat = models.Category.query.get(getcid())
      if not cat:
        raise ValidationError('No such category.')
      return cat
    try:
      op = flask.request.form.get('op')
      if op == 'new':
        cat = models.Category.create(
            flask.request.form.get('name'),
            flask.request.form.get('description'))
        if cat:
          flask.flash('%s created.' % cat.name, 'success')
      else:
        cat = getcat()
        if op == 'edit':
          cat.name = flask.request.form.get('name')
          cat.description = flask.request.form.get('description')
          models.commit()
        elif op == 'delete':
          cat.delete()
          flask.flash('Deleted.', 'success')
        elif op == 'lock':
          cat.unlocked = False
          models.commit()
        elif op == 'unlock':
          cat.unlocked = True
          models.commit()
        else:
          raise ValidationError('Invalid operation.')
    except ValidationError as ex:
      flask.flash(str(ex), 'danger')
  return flask.render_template('admin/categories.html',
      categories=models.Category.query.all())


@app.route('/admin/challenges/<int:cid>')
@login_required
@admin_required
def admin_challenges(cid):
  category = models.Category.query.get(cid)
  if not category:
    flask.flash('No such category.')
    return flask.redirect(flask.url_for('admin_categories'))
  challenges = models.Challenge.query.filter(models.Challenge.category ==
      category).all()
  return flask.render_template('admin/challenges.html',
      category=category, challenges=challenges)


@app.route('/admin/challenge/<op>', methods=['GET', 'POST'])
@app.route('/admin/challenge/<op>/<int:cid>', methods=['GET', 'POST'])
@login_required
@admin_required
@csrfutil.csrf_protect
def admin_challenge(op, cid=None):
  categories = models.Category.query.all()
  if cid:
    challenge = models.Challenge.query.get(cid)
    if not challenge:
      flask.flash('No such challenge.')
      return flask.redirect(flask.url_for('admin_categories'))
    cat = challenge.cat_cid
  else:
    challenge = None
    cat = int(flask.request.values.get('cat', 0))
  if flask.request.method == 'POST':
    try:
      name = flask.request.form.get('name')
      description = flask.request.form.get('description')
      points = int(flask.request.form.get('points', 0))
      answer = flask.request.form.get('answer')
      cat_cid = int(flask.request.form.get('category'))
      unlocked = flask.request.form.get('unlocked')
      for fname, field in (('name', 'Name'), ('description', 'Description'),
          ('points', 'Points'), ('category', 'Category')):
        if not flask.request.form.get(fname):
          raise ValidationError('%s is required.' % field)
      if op == 'new':
        challenge = models.Challenge.create(
            name, description, points, answer, cat_cid,
            True if unlocked else False)
        if challenge:
          flask.flash('Challenge created.', 'success')
          return flask.redirect(flask.url_for(
            'admin_challenge', op='edit', cid=challenge.cid))
        else:
          flask.flash('Error creating challenge.', 'danger')
      elif op == 'edit':
        challenge.name = name
        challenge.description = description
        challenge.points = points
        challenge.cat_cid = cat_cid
        challenge.unlocked = True if flask.request.form.get('unlocked') else False
        if answer:
          challenge.change_answer(answer)
        models.commit()
      elif op == 'delete':
        challenge.delete()
        flask.flash('Challenge deleted.', 'success')
        return flask.redirect(flask.url_for(
          'admin_challenges', cid=challenge.cat_cid))
      else:
        raise ValidationError('Unknown operation %s' % op)
    except ValidationError as ex:
      flask.flash(str(ex), 'danger')
  return flask.render_template('admin/challenge.html',
      cat=cat,
      op=op,
      categories=categories,
      challenge=challenge)

@app.route('/admin/backup/challenges')
@login_required
@admin_required
def admin_challenge_backup():
  categories = {}
  challenges = []
  for cat in models.Category.query.all():
    categories[cat.cid] = {
        'name': cat.name,
        'description': cat.description
        }
    for q in cat.challenges:
      challenges.append({
        'category': cat.cid,
        'name': q.name,
        'description': q.description,
        'points': q.points,
        'answer_hash': q.answer_hash
        })
  response = flask.jsonify(categories=categories,
      challenges=challenges)
  response.headers['Content-Disposition'] = 'attachment; filename=challenges.json'
  return response


@app.route('/admin/backup/challenges/restore', methods=['GET', 'POST'])
@login_required
@admin_required
@csrfutil.csrf_protect
def admin_challenge_restore():
  if flask.request.method == 'POST':
    _perform_admin_challenge_restore()
    return flask.redirect(flask.url_for(flask.request.endpoint))
  return flask.render_template('admin/restore_challenges.html')


def _perform_admin_challenge_restore():
  jsfile = flask.request.files.get('restorefile')
  if not jsfile:
    flask.flash('No JSON file was sent.', 'warning')
    return
  try:
    data = json.load(jsfile)
  except ValueError:
    flask.flash('Invalid JSON!', 'danger')
    return

  deleted = False
  if flask.request.form.get('replace') == 'True':
    models.Category.query.delete()
    models.Challenge.query.delete()
    deleted = True

  cats = {}
  for catid, cat in data['categories'].iteritems():
    newcat = models.Category()
    for f in ('name', 'description'):
      setattr(newcat, f, cat[f])
    models.db.session.add(newcat)
    cats[int(catid)] = newcat
  
  for challenge in data['challenges']:
    newchall = models.Challenge()
    for f in ('name', 'description', 'points', 'answer_hash'):
      setattr(newchall, f, challenge[f])
    newchall.category = cats[challenge['category']]
    models.db.session.add(newchall)
  
  models.commit()
  if deleted:
    flask.flash('Deleted old categories & challenges.', 'success')
  flask.flash('%d Categories and %d Challenges imported.' %
      (len(data['categories']), len(data['challenges'])),
      'success')
