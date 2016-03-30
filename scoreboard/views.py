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
import os
from werkzeug import exceptions

from scoreboard.app import app
from scoreboard import attachments
from scoreboard import models
from scoreboard import utils


_VIEW_CACHE = {}


@app.errorhandler(404)
def handle_404(ex):
    """Handle 404s, sending index.html for unhandled paths."""
    path = flask.request.path[1:]
    try:
        return app.send_static_file(path)
    except (exceptions.NotFound, UnicodeEncodeError):
        if '.' not in path and not path.startswith('api/'):
            app.logger.info('%s -> index.html', path)
            return render_index()
        return '404 Not Found', 404


# Needed because emails with a "." in them prevent 404 handler from working
@app.route('/pwreset/<path:unused>')
def render_pwreset(unused):
    return render_index()


@app.route('/')
@app.route('/index.html')
def render_index():
    """Render index.

    Do not include any user-controlled content to avoid XSS!
    """
    try:
        tmpl = _VIEW_CACHE['index']
    except KeyError:
        minify = not app.debug and os.path.exists(
                os.path.join(app.static_folder, 'js/app.min.js'))
        tmpl = flask.render_template('index.html', minify=minify)
        _VIEW_CACHE['index'] = tmpl
    return flask.make_response(tmpl, 200)


@app.route('/attachment/<filename>')
@utils.login_required
def download(filename):
    """Download an attachment."""

    attachment = models.Attachment.query.get_or_404(filename)
    if not attachment.challenge.unlocked:
        flask.abort(404)
    app.logger.info('Download of %s by %r.', attachment, flask.g.user)

    return attachments.send(attachment)


@app.route('/createdb')
def createdb():
    """Create database schema without CLI access.

    Useful for AppEngine and other container environments.
    Should be safe to be exposed, as operation is idempotent and does not
    clear any data.
    """
    try:
        models.db.create_all()
        return 'Tables created.'
    except Exception as ex:
        app.logger.exception('Failed creating tables: %s', str(ex))
        return 'Failed creating tables: see log.'
