# Copyright 2016 Google Inc. All Rights Reserved.
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

import base64
import datetime
import flask
import functools
import hashlib
import hmac
import pytz
import sys
import time

try:
    import urlparse
except ImportError:
    from urllib import parse as urlparse

from random import SystemRandom

from scoreboard import errors
from scoreboard import main

app = main.get_app()
random = SystemRandom()

# Use dateutil if available
try:
    from dateutil import parser as dateutil
except ImportError:
    dateutil = None


def is_logged_in():
    try:
        return flask.g.uid is not None
    except AttributeError:
        return False


def login_required(f):
    """Decorator to require login for a method."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            raise errors.AccessDeniedError('You must be logged in.')
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    """Decorator to require admin for a method."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            if not flask.g.admin:
                app.logger.error(
                        'Attempt by non-admin to access '
                        '@admin_required resource.')
                flask.abort(403)
        except AttributeError:
            app.logger.error(
                    'AttributeError by non-admin to access '
                    '@admin_required resource.')
            flask.abort(403)
        return f(*args, **kwargs)
    return login_required(wrapper)


def team_required(f):
    """Require that they are a member of a team."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if not flask.g.tid:
            app.logger.warning(
                'Team request received for player without team.')
            flask.abort(400)
        return f(*args, **kwargs)
    return login_required(wrapper)


def is_admin():
    """Check if current user is an admin."""
    try:
        return flask.g.admin
    except AttributeError:
        return False


def session_for_user(user):
    """Construct session for current user."""
    flask.g.user = user
    flask.g.team = user.team
    flask.g.uid = user.uid
    flask.g.tid = user.team.tid if user.team else None
    flask.g.admin = user.admin
    flask.session['user'] = user.uid
    flask.session['team'] = user.team.tid if user.team else None
    flask.session['admin'] = user.admin
    expires = app.config.get('SESSION_EXPIRATION_SECONDS', 0)
    if expires:
        flask.session['expires'] = int(time.time() + expires)


def get_required_field(name, verbose_name=None):
    """Retrieve a field or raise an error."""

    try:
        return flask.request.form[name]
    except KeyError:
        verbose_name = verbose_name or name
        raise errors.ValidationError('%s is a required field.' % verbose_name)


def parse_bool(b):
    b = b.lower()
    return b in ('true', '1')


def compare_digest(a, b):
    """Intended to be a constant-time comparison."""
    if hasattr(hmac, 'compare_digest'):
        return hmac.compare_digest(a, b)
    return hashlib.sha1(a).digest() == hashlib.sha1(b).digest()


def absolute_url(path):
    """Build an absolute URL.  Not safe for untrusted input."""
    return urlparse.urljoin(flask.request.host_url, path)


def generate_id():
    """Generate a unique identifier for the database"""
    return int(random.getrandbits(48))


def normalize_input(answer):
    """Take a string and normalize it to a standard format."""
    return answer.strip()


def validate_proof_of_work(val, key, nbits):
    """Assert that the proof of work function has nbits 0s.

    The key should be urlsafe-base64 encoded.
    """
    key = urlsafe_b64decode_nopadding(key)
    if len(key) < 32:
        return False
    val = to_bytes(val)
    mac = hmac.new(key, val, digestmod=hashlib.sha256).digest()

    def _ord(v):
        if isinstance(v, int):
            return v
        return ord(v)

    while nbits >= 8:
        if _ord(mac[0]) != 0:
            return False
        nbits -= 8
        mac = mac[1:]
    if nbits:
        mask = 2**nbits - 1
        if _ord(mac[0]) & mask:
            return False
    return True


def urlsafe_b64decode_nopadding(val):
    """Deal with unpadded urlsafe base64."""
    # Yes, it accepts extra = characters.
    return base64.urlsafe_b64decode(str(val) + '===')


def to_bytes(val):
    if sys.version_info.major == 3:
        unicode = str
        if isinstance(val, str):
            return bytes(val, 'utf-8')
        if isinstance(val, bytes):
            return val
    if isinstance(val, unicode):
        return val.encode('utf-8')
    return val


class GameTime(object):
    """Manage start/end times for the game."""

    @classmethod
    def setup(cls):
        """Get start and end time."""
        cls.start, cls.end = app.config.get('GAME_TIME')
        if isinstance(cls.start, str):
            cls.start = cls._parsedate(cls.start)
        if isinstance(cls.end, str):
            cls.end = cls._parsedate(cls.end)

    @classmethod
    def countdown(cls, end=False):
        """Time remaining to start or end."""
        until = cls.end if end else cls.start
        if until is None:
            return None
        return until - datetime.datetime.utcnow()

    @classmethod
    def state(cls, now=None):
        if not now:
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
    def over(cls):
        """Has the game ended?"""
        state = cls.state()
        return state == 'AFTER'

    @classmethod
    def require_open(cls, f, after_end=False, or_admin=True):
        """Decorator for requiring the game is open."""
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if (cls.open(after_end) or
                    (or_admin and flask.g.admin)):
                return f(*args, **kwargs)
            raise errors.AccessDeniedError(cls.message())
        return wrapper

    @classmethod
    def require_started(cls, f):
        """Decorator for requiring the game has started."""
        return cls.require_open(f, after_end=True)

    @classmethod
    def require_not_started(cls, f):
        """Decorator for requiring the game has not started."""
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if cls.state() == "BEFORE":
                return f(*args, **kwargs)
            raise errors.AccessDeniedError(cls.message())
        return wrapper

    @classmethod
    def require_submittable(cls, f):
        """Decorator for requiring that the game may be submitted to."""
        return cls.require_open(
                f, after_end=app.config.get('SUBMIT_AFTER_END'))

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
        """Return a UTC non-TZ-aware datetime from a string."""
        if dateutil:
            dt = dateutil.parse(datestr)
            if dt.tzinfo:
                dt = dt.astimezone(pytz.UTC).replace(tzinfo=None)
            return dt
        # TODO: parse with strptime
        raise RuntimeError('No parser available.')


GameTime.setup()
require_gametime = GameTime.require_open
require_started = GameTime.require_started
require_not_started = GameTime.require_not_started
require_submittable = GameTime.require_submittable
