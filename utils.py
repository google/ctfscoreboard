import datetime
import flask
import functools
from app import app

# Use dateutil if available
try:
  from dateutil import parser as dateutil
except ImportError:
  dateutil = None

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
