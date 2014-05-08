# Copyright 2014 David Tomaschik <david@systemoverlord.com>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import errors
import flask
import functools

from app import app
import models

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
      app.logger.warning('Team request received for player without team.')
      flask.abort(400)
    return f(*args, **kwargs)
  return login_required(wrapper)


## Utility functions
def get_required_field(name, verbose_name=None):
  try:
    return flask.request.form[name]
  except KeyError:
    verbose_name = verbose_name or name
    raise errors.ValidationError('%s is a required field.' % verbose_name)


def parse_bool(b):
  b = b.lower()
  return b in ('true', '1')


def access_team(team):
  """Permission to team."""
  if flask.g.user and flask.g.user.admin:
    return True
  try:
    team = team.tid
  except AttributeError:
    pass
  if flask.g.team and flask.g.team.tid == team:
    return True
  return False


## Game time settings
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
  def require_open(cls, f, after_end=False, or_admin=True):
    """Decorator for requiring the game is open."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
      if cls.open(after_end) or (or_admin and flask.g.user and flask.g.user.admin):
        return f(*args, **kwargs)
      raise errors.AccessDeniedError(cls.message())
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
