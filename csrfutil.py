
import base64
import flask
import functools
import hashlib
import hmac
import jinja2
import struct
import time

from app import app


def _get_csrf_token(user=None, path=None, expires=None):
  path = path or flask.request.endpoint
  user = user or flask.session.get('user', flask.request.remote_addr)
  expires = expires or time.time() + 60*60*24
  expires_bytes = struct.pack('<I', expires)
  msg = '%s:%s:%s' % (user, path, expires_bytes)
  sig = hmac.new(app.config['SECRET_KEY'], msg, hashlib.sha256).digest()
  return expires_bytes + sig

def get_csrf_token(*args, **kwargs):
  return base64.b64encode(_get_csrf_token(*args, **kwargs))


def verify_csrf_token(token, user=None, path=None):
  token = base64.b64decode(token)
  expires = struct.unpack('<I', token[:4])[0]
  return token == _get_csrf_token(user, path, expires)


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


@app.context_processor
def csrf_context_processor():
  return {
      'csrftoken': get_csrf_token,
      'csrffield': get_csrf_field,
      }
