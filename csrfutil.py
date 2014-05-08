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

import base64
import flask
import functools
import hashlib
import hmac
import jinja2
import struct
import time

from app import app
import errors


def _get_csrf_token(user=None, expires=None):
  user = user or flask.session.get('user', flask.request.remote_addr)
  expires = expires or time.time() + 60*60*24
  expires_bytes = struct.pack('<I', expires)
  msg = '%s:%s' % (user, expires_bytes)
  sig = hmac.new(app.config['SECRET_KEY'], msg, hashlib.sha256).digest()
  return expires_bytes + sig

def get_csrf_token(*args, **kwargs):
  return base64.b64encode(str(_get_csrf_token(*args, **kwargs)), '_-')


def verify_csrf_token(token, user=None):
  token = base64.b64decode(str(token), '_-')
  expires = struct.unpack('<I', token[:4])[0]
  return token == _get_csrf_token(user, expires)


def csrf_protect(f):
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
  token = get_csrf_token(*args, **kwargs)
  field = jinja2.Markup('<input type="hidden" name="csrftoken" value="%s" />')
  return field % token


@app.before_request
def csrf_protection_request():
  if flask.request.method in ('GET', 'HEAD'):
    return
  header = flask.request.headers.get('X-XSRF-TOKEN')
  token = header or flask.request.values.get('csrftoken')
  if not token or not verify_csrf_token(token):
    app.logger.warning('CSRF Validation Failed')
    flask.abort(403)


@app.after_request
def add_csrf_protection(resp):
  resp.set_cookie('XSRF-TOKEN', get_csrf_token())
  return resp


@app.context_processor
def csrf_context_processor():
  return {
      'csrftoken': get_csrf_token,
      'csrffield': get_csrf_field,
      }
