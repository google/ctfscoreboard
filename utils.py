import datetime
import errors
import flask
import functools
from app import app

# Use dateutil if available
try:
  from dateutil import parser as dateutil
except ImportError:
  dateutil = None


# Setup flask.g
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


# Helper decorators
def login_required(f):
  @functools.wraps(f)
  def wrapper(*args, **kwargs):
    if not flask.g.user:
      raise errors.AccessDeniedError('You must be logged in.')
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
  return login_required(wrapper)


def team_required(f):
  """Require that they are a member of a team."""
  @functools.wraps(f)
  def wrapper(*args, **kwargs):
    if not flask.g.team:
      flask.abort(400)
    return f(*args, **kwargs)
  return login_required(wrapper)


class GameTime(object):

  @classmethod
  def setup(cls):
    """Get start and end time."""
    cls.start, cls.end = app.config.get('GAME_TIME', (None, None))
    if isinstance(cls.start, basestring):
      cls.start = cls._parsedate(cls.start)
    if isinstance(cls.end, basestring):
      cls.end = cls._parsedate(cls.end)

  @classmethod
  def countdown(cls, end=False):
    """Time remaining to start or end."""
    until = cls.end if end else cls.start
    if until is None:
      return None
    return until - datetime.datetime.utcnow()

  @classmethod
  def state(cls):
    now = datetime.datetime.utcnow()
    if cls.start and cls.start > now:
      return 'BEFORE'
    if cls.end and cls.end < now:
      return 'AFTER'
    return 'DURING'

  @classmethod
  def open(cls, after_end=False):
    """Is the game open?  If after_end, keeps open."""
    state = cls.state()
    if state == 'DURING' or (after_end and state == 'AFTER'):
      return True
    return False

  @classmethod
  def require_open(cls, f, after_end=False):
    """Decorator for requiring the game is open."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
      if cls.open(after_end):
        return f(*args, **kwargs)
      return flask.make_response(
          flask.render_template('error.html',
            message=cls.message(), title='Forbidden'), 403)
    return wrapper

  @classmethod
  def message(cls):
    state = cls.state()
    if state == 'BEFORE':
      return 'Game begins in %s.' % str(cls.countdown())
    if state == 'AFTER':
      return 'Game is over.'
    return '%s left in the game.' % str(cls.countdown(end=True))

  @staticmethod
  def _parsedate(datestr):
    if dateutil:
      return dateutil.parse(datestr)
    # TODO: parse with strptime
    raise RuntimeError('No parser available.')

GameTime.setup()
require_gametime = GameTime.require_open


@app.context_processor
def util_contexts():
  return dict(gametime=GameTime)
