import flask
import functools
import json
import re
from sqlalchemy import exc

from app import app
import errors
import models
import utils


def user_login(email=None, password=None):
  email = email or flask.request.form.get('email')
  password = password or flask.request.form.get('password')
  if email and password:
    user = models.User.login_user(email, password)
    if user:
      flask.session['user'] = user.uid
      return user


def register_user(email, nick, password, team_id=None,
    team_name=None, team_code=None):
  """Registers a player.

  Arguments:
    email: User's email
    nick: User's nick
    password: Player's password
    password2: Validation of password
    team_id: Id# of team, or None to create new team.
    team_name: Name of new team.
    team_code: Validation code to join team.
  """
  if not re.match(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]{2,4}$',
      email):
    raise errors.ValidationError('Invalid email address.')
  if app.config.get('TEAMS'):
    if not team_id:
      try:
        team = models.Team.create(team_name)
      except exc.IntegrityError:
        models.db.session.rollback()
        raise errors.ValidationError('Team already exists!')
    else:
      team = models.Team.query.get(int(team_id))
      if not team or team_code.lower() != team.code.lower():
        raise errors.ValidationError('Invalid team selection or team code.')
  else:
    team = None
  try:
    if not team:
      team = models.Team.create(nick)
    user = models.User.create(email, nick, password, team=team)
  except exc.IntegrityError:
    models.db.session.rollback()
    raise errors.ValidationError('Duplicate email/nick.')
  flask.session['user'] = user.uid
  app.logger.info('User %s <%s> registered from IP %s.',
      nick, email, flask.request.access_route[0])
  return user


@utils.require_gametime
def submit_answer(cid, answer):
  """Submits an answer.

  Returns:
    Number of points awarded for answer.
  """
  try:
    challenge = models.Challenge.query.get(cid)
    if not challenge.unlocked:
      raise errors.AccessDeniedError('Challenge is locked!')
    if challenge.verify_answer(answer):
      # Deductions for hints
      hints = models.UnlockedHint.query.filter(
          models.UnlockedHint.team == flask.g.team).all()
      deduction = sum(h.hint.cost for h in hints if h.hint.challenge_cid==cid)
      points = challenge.points - deduction
      flask.g.team.score += points
      models.Answer.create(challenge, flask.g.team, answer)
      correct = 'CORRECT'
      return points
    else:
      correct = 'WRONG'
      raise errors.InvalidAnswerError('Really?  Haha no....')
  finally:
    app.challenge_log.info(
        '[%s] Player %s <%s>(%d)/Team %s(%d) submitted "%s" for Challenge '
        '%s<%d>: %s', flask.request.access_route[0],
        flask.g.user.nick, flask.g.user.email, flask.g.user.uid,
        flask.g.team.name, flask.g.team.tid, answer, challenge.name,
        challenge.cid, correct)


@utils.require_gametime
def unlock_hint(hid):
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
  return hint
