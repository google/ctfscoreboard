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

import flask
import logging
import re
from werkzeug import exceptions
from werkzeug.utils import ImportStringError


app = flask.Flask('scoreboard')
# Handle both standalone and as part of pwnableweb
try:
  app.config.from_object('scoreboard.config')  # Load from config.py
except ImportStringError:
  app.config.from_object('config')  # Load from config.py

# Main logger
if not app.debug:
  handler = logging.FileHandler(
      app.config.get('LOGFILE', '/tmp/scoreboard.wsgi.log'))
  handler.setLevel(logging.INFO)
  handler.setFormatter(logging.Formatter(
      '%(asctime)s %(levelname)8s [%(filename)s:%(lineno)d] %(message)s'))
  app.logger.addHandler(handler)

# Challenge logger
handler = logging.FileHandler(
    app.config.get('CHALLENGELOG', '/tmp/scoreboard.challenge.log'))
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger = logging.getLogger('scoreboard')
logger.addHandler(handler)
app.challenge_log = logger

# Install a default error handler
error_titles = {
    403: 'Forbidden',
    404: 'Not Found',
    500: 'Internal Error',
    }
def api_error_handler(ex):
  try:
    status_code = ex.code
  except AttributeError:
    status_code = 500
  if status_code == 404:
    path = flask.request.path[1:]
    try:
      # Try to serve static
      return app.send_static_file(path)
    except exceptions.NotFound:
      # Send index.html for other paths
      if not re.search('\.(js|css|gif|png|jpg|jpeg)$', path):
        print '%s -> index.html' % path
        return app.send_static_file('index.html')
  if flask.request.path.startswith('/api/'):
    print str(ex)
    resp = flask.jsonify(message=str(ex))
    resp.status_code = status_code
    return resp
  return flask.make_response(
      flask.render_template('error.html', exc=ex,
        title=error_titles.get(status_code, 'Error')), status_code)

for c in exceptions.default_exceptions.iterkeys():
  app.register_error_handler(c, api_error_handler)
