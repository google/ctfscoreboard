import flask
import functools
import json
import re
from sqlalchemy import exc

from app import app
import csrfutil
import controllers
import errors
import models
import utils


#@app.route('/login', methods=['GET', 'POST'])
@csrfutil.csrf_protect
def login():
  if flask.request.method == 'POST':
    user = controllers.user_login()
    if user:
      return flask.redirect(flask.url_for('challenges'))
    flask.flash('Invalid username/password.')
  return flask.render_template('login.html')


#@app.route('/logout', methods=['GET', 'POST'])
def logout():
  flask.session['user'] = None
  flask.flash('You have successfully logged out.', 'success')
  return flask.redirect(flask.url_for('login'))


#@app.route('/register', methods=['GET', 'POST'])
def register():
  if flask.request.method == 'POST':
    try:
      email = utils.get_required_field('email')
      nick = utils.get_required_field('nick')
      password = utils.get_required_field('password')
      password2 = utils.get_required_field('password2')
      team_id = flask.request.form.get('team')
      team_name = flask.request.form.get('team_name')
      team_code = flask.request.form.get('team_code')
      user = controllers.register_user(email, nick, password, password2,
          team_id, team_name, team_code)
      flask.flash('Registration successful.', 'success')
      return flask.redirect(flask.url_for('challenges'))
    except errors.ValidationError as ex:
      flask.flash(str(ex), 'danger')
  return flask.render_template('register.html',
      teams=models.Team.query.all())


#@app.route('/scoreboard')
def scoreboard():
  return flask.render_template('scoreboard.html',
      teams=models.Team.enumerate())


#@app.route('/challenges')
@utils.login_required
@utils.require_gametime
def challenges():
  return flask.render_template('challenges.html',
      categories=models.Category.query.all())


#@app.route('/challenges/<slug>')
@utils.login_required
@utils.require_gametime
def challenges_by_cat(slug):
  categories = models.Category.query.all()
  cfilter = [c for c in categories if c.slug==slug]
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
      challenges=category.get_challenges().all())


#@app.route('/submit/<int:cid>', methods=['POST'])
@utils.team_required
@csrfutil.csrf_protect
@utils.require_gametime
def submit(cid):
  answer = flask.request.form.get('answer')
  try:
    points = controller.submit_answer(answer)
    flask.flash('Congratulations!  %d points awarded.' % points,
        'success')
  except errors.AccessDeniedError:
    flask.flash('Really?  Haha no...', 'warning')
  return flask.redirect(flask.url_for(
    'challenges_by_cat', slug=challenge.category.slug))


#@app.route('/profile', methods=['GET', 'POST'])
@utils.login_required
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


#@app.route('/unlock_hint', methods=['POST'])
@utils.team_required
@csrfutil.csrf_protect
@utils.require_gametime
def unlock_hint():
  hid = flask.request.form['hid']
  hint = models.Hint.query.get(int(hid))
  if not hint:
    flask.abort(404)
  hint.unlock(flask.g.team)
  flask.flash('Hint unlocked.', 'success')
  logstr = 'Player %s/%s<%d>/Team %s<%d> unlocked hint %d for Challenge %s<%d>'
  logstr %= (flask.g.user.nick, flask.g.user.email, flask.g.user.uid,
      flask.g.team.name, flask.g.team.tid, hint.hid, hint.challenge.name,
      hint.challenge.cid)
  app.challenge_log.info(logstr)
  return flask.redirect(flask.request.form['redir'])


# Admin UI
#@app.route('/admin/makemeadmin')
@utils.login_required
def makemeadmin():
  # Only works if no other admins exist
  if models.User.query.filter(models.User.admin == True).count():
    flask.abort(403)
  flask.g.user.promote()
  models.commit()
  return flask.redirect(flask.url_for('index'))


#@app.route('/admin/categories', methods=['GET', 'POST'])
@utils.admin_required
@csrfutil.csrf_protect
def admin_categories():
  if flask.request.method == 'POST':
    def getcid():
      try:
        return int(flask.request.form.get('cid'))
      except TypeError:
        raise errors.ValidationError('Invalid category id.')
    def getcat():
      cat = models.Category.query.get(getcid())
      if not cat:
        raise errors.ValidationError('No such category.')
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
          raise errors.ValidationError('Invalid operation.')
    except errors.ValidationError as ex:
      flask.flash(str(ex), 'danger')
  return flask.render_template('admin/categories.html',
      categories=models.Category.query.all())


#@app.route('/admin/challenges')
#@app.route('/admin/challenges/<int:cid>')
@utils.admin_required
def admin_challenges(cid=None):
  if cid:
    category = models.Category.query.get(cid)
    if not category:
      flask.flash('No such category.')
      return flask.redirect(flask.url_for('admin_categories'))
    challenges = models.Challenge.query.filter(models.Challenge.category ==
        category).all()
  else:
    category = None
    challenges = models.Challenge.query.all()
  return flask.render_template('admin/challenges.html',
      category=category, challenges=challenges)


#@app.route('/admin/challenge/<op>', methods=['GET', 'POST'])
#@app.route('/admin/challenge/<op>/<int:cid>', methods=['GET', 'POST'])
@utils.admin_required
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
    # lock/unlock are AJAX calls
    if op == 'lock':
      challenge.unlocked = False
      models.commit()
      return 'locked'
    elif op == 'unlock':
      challenge.unlocked = True
      models.commit()
      return 'unlocked'
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
          raise errors.ValidationError('%s is required.' % field)
      if op == 'new':
        challenge = models.Challenge.create(
            name, description, points, answer, cat_cid,
            True if unlocked else False)
        if challenge:
          _challenge_update_hints(challenge)
          models.commit()
          flask.flash('Challenge created.', 'success')
          return flask.redirect(flask.url_for('admin_challenges',
              cid=cat if cat else None))
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
        _challenge_update_hints(challenge)
        models.commit()
        flask.flash('Challenge updated.', 'success')
      elif op == 'delete':
        challenge.delete()
        flask.flash('Challenge deleted.', 'success')
        return flask.redirect(flask.url_for(
          'admin_challenges', cid=challenge.cat_cid))
      else:
        raise errors.ValidationError('Unknown operation %s' % op)
    except errors.ValidationError as ex:
      flask.flash(str(ex), 'danger')
  return flask.render_template('admin/challenge.html',
      cat=cat,
      op=op,
      categories=categories,
      challenge=challenge)


def _challenge_update_hints(challenge):
  # Delete removed
  hints = [int(x) for x in flask.request.form.getlist('hint')]
  for h in challenge.hints:
    if h.hid not in hints:
      models.db.session.delete(h)
    else:
      h.hint = flask.request.form.get('hint-'+str(h.hid)+'-hint')
      h.cost = int(flask.request.form.get('hint-'+str(h.hid)+'-cost'))
  for text,cost in zip(
      flask.request.form.getlist('hint-new-hint'),
      flask.request.form.getlist('hint-new-cost')):
    if not text or not cost:
      continue
    cost = int(cost)
    hint = models.Hint()
    hint.hint = text
    hint.cost = cost
    hint.challenge = challenge
    models.db.session.add(hint)


@app.route('/admin/backup/challenges')
@utils.admin_required
def admin_challenge_backup():
  categories = {}
  challenges = []
  for cat in models.Category.query.all():
    categories[cat.cid] = {
        'name': cat.name,
        'description': cat.description
        }
    for q in cat.challenges:
      hints = []
      for h in q.hints:
        hints.append({
          'hint': h.hint,
          'cost': h.cost,
          })
      challenges.append({
        'category': cat.cid,
        'name': q.name,
        'description': q.description,
        'points': q.points,
        'answer_hash': q.answer_hash,
        'hints': hints,
        })
  response = flask.jsonify(categories=categories,
      challenges=challenges)
  response.headers['Content-Disposition'] = 'attachment; filename=challenges.json'
  return response


@app.route('/admin/backup/challenges/restore', methods=['GET', 'POST'])
@utils.admin_required
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
    models.Hint.query.delete()
    models.Challenge.query.delete()
    models.Category.query.delete()
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
    for h in challenge.get('hints', []):
      hint = models.Hint()
      hint.challenge = newchall
      hint.hint = h['hint']
      hint.cost = int(h['cost'])
      models.db.session.add(hint)
  
  models.commit()
  if deleted:
    flask.flash('Deleted old categories & challenges.', 'success')
  flask.flash('%d Categories and %d Challenges imported.' %
      (len(data['categories']), len(data['challenges'])),
      'success')


#@app.route('/admin/teams')
@utils.admin_required
def admin_teams():
  if not app.config.get('TEAMS'):
    flask.abort(404)
  return flask.render_template('admin/teams.html',
      teams=models.User.query.order_by(models.User.name).all())


#@app.route('/admin/team/<int:tid>', methods=['GET', 'POST'])
@utils.admin_required
@csrfutil.csrf_protect
def admin_team(tid):
  if not app.config.get('TEAMS'):
    flask.abort(404)
  team = models.Team.query.get(tid)
  if not team:
    flask.abort(404)
  # TODO: support updates
  return flask.render_template('admin/team.html', team=team)


#@app.route('/admin/users')
@utils.admin_required
def admin_users():
  users = models.User.query.order_by(
      models.User.nick).all()
  return flask.render_template('admin/users.html', users=users)


#@app.route('/admin/user/<int:uid>', methods=['GET', 'POST'])
@csrfutil.csrf_protect
@utils.admin_required
def admin_user(uid):
  user = models.User.query.get(uid)
  if not user:
    flask.flash('No such user.', 'warning')
    return flask.render_template('error.html')
  if flask.request.method == 'POST':
    # TODO: support other edits
    if flask.request.form.get('admin'):
      user.promote()
    else:
      # TODO: demoted users should get a team
      user.admin = False
    if (not app.config.get('TEAMS') and
        flask.request.form.get('score') is not None):
      score = int(flask.request.form.get('score'))
      orig_score = int(flask.request.form.get('orig_score'))
      if orig_score != user.team.score:
        flask.flash('Race condition updating score.', 'warning')
      else:
        user.team.score = score
    models.commit()
    flask.flash('User updated.')
    return flask.redirect(flask.url_for(flask.request.endpoint, uid=uid))
  return flask.render_template('admin/user.html', user=user)
