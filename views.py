import flask
import json

from app import app
import csrfutil
import models
import utils


@app.route('/admin/backup/challenges')
@utils.admin_required
def admin_challenge_backup():
  categories = {}
  for cat in models.Category.query.all():
    challenges = []
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
    categories[cat.cid] = {
        'name': cat.name,
        'description': cat.description,
        'challenges': challenges,
        }
  response = flask.jsonify(categories=categories)
  response.headers['Content-Disposition'] = 'attachment; filename=challenges.json'
  return response


@app.route('/admin/backup/challenges/restore', methods=['POST'])
@utils.admin_required
@csrfutil.csrf_protect
def admin_challenge_restore():
  # TODO: angularify
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
  
    for challenge in cat['challenges']:
      newchall = models.Challenge()
      for f in ('name', 'description', 'points', 'answer_hash'):
        setattr(newchall, f, challenge[f])
      newchall.category = newcat
      models.db.session.add(newchall)
      for h in challenge.get('hints', []):
        hint = models.Hint()
        hint.challenge = newchall
        hint.hint = h['hint']
        hint.cost = int(h['cost'])
        models.db.session.add(hint)
  
  models.commit()
  return flask.redirect('/admin/categories')
