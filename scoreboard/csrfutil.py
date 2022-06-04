# Copyright 2016 Google LLC. All Rights Reserved.
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
import binascii
import flask
import functools
import hashlib
import hmac
import struct
import time

from markupsafe import Markup

from scoreboard import main
from scoreboard import utils

app = main.get_app()

b64_vals = utils.to_bytes('_-')


def _get_csrf_token(user=None, expires=None):
    user = user or flask.session.get('user', flask.request.remote_addr)
    expires = expires or int(time.time()) + 60 * 60 * 24
    expires_bytes = struct.pack('<I', expires)
    msg = utils.to_bytes('%s:' % user) + expires_bytes
    key = utils.to_bytes(app.config.get('SECRET_KEY'))
    sig = hmac.new(key, msg, hashlib.sha256).digest()
    return expires_bytes + sig


def get_csrf_token(*args, **kwargs):
    """Returns a URL-safe base64 CSRF token."""
    return base64.b64encode(utils.to_bytes(
        _get_csrf_token(*args, **kwargs)), b64_vals).decode('utf-8')


def verify_csrf_token(token, user=None):
    """Verify a token for a user."""
    try:
        token = base64.b64decode(str(token), b64_vals)
    except (binascii.Error, TypeError):
        return False
    expires = struct.unpack('<I', token[:4])[0]
    if expires < time.time():
        return False
    return token == _get_csrf_token(user, expires)


def csrf_protect(f):
    """Decorator to add CSRF protection to a request handler."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        if flask.request.method == 'POST':
            token = flask.request.values.get('csrftoken')
            if not token or not verify_csrf_token(token):
                app.logger.warning('CSRF Validation Failed.')
                flask.abort(403)
        return f(*args, **kwargs)
    return wrapper


def get_csrf_field(*args, **kwargs):
    """Render a CSRF field."""
    token = get_csrf_token(*args, **kwargs)
    field = Markup(
        '<input type="hidden" name="csrftoken" value="%s" />')
    return field % token


@app.before_request
def csrf_protection_request():
    """Add CSRF Protection to all non-GET/non-HEAD requests."""
    if flask.request.method in ('GET', 'HEAD'):
        return
    if app.config.get('TESTING'):
        return
    header = flask.request.headers.get('X-XSRF-TOKEN')
    token = header or flask.request.values.get('csrftoken')
    if not token or not verify_csrf_token(token):
        app.logger.warning('CSRF Validation Failed')
        flask.abort(403)


@app.after_request
def add_csrf_protection(resp):
    """Add the XSRF-TOKEN cookie to all outgoing requests."""
    resp.set_cookie('XSRF-TOKEN', get_csrf_token())
    return resp


@app.context_processor
def csrf_context_processor():
    """Add CSRF token and field to all rendering contexts."""
    return {
        'csrftoken': get_csrf_token,
        'csrffield': get_csrf_field,
    }
