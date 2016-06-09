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

import flask
import logging
import os
from werkzeug import exceptions
import flask_scss

from scoreboard import logger


def on_appengine():
    """Returns true if we're running on AppEngine."""
    runtime = os.environ.get('SERVER_SOFTWARE', '')
    return (runtime.startswith('Development/') or
            runtime.startswith('Google App Engine/'))


def create_app(config=None):
    app = flask.Flask(
            'scoreboard',
            static_folder='../static',
            template_folder='../templates',
            )
    app.config.from_object('scoreboard.config_defaults.Defaults')
    if config is not None:
        app.config.update(**config)
    else:
        app.config.from_object('config')  # Load from config.py

    log_formatter = logger.Formatter(
            '%(asctime)s %(levelname)8s [%(filename)s:%(lineno)d] %(client)s %(message)s')
    # log to files unless on AppEngine
    if not on_appengine():
        # Main logger
        if not app.debug:
            handler = logging.FileHandler(
                app.config.get('LOGFILE', '/tmp/scoreboard.wsgi.log'))
            handler.setLevel(logging.INFO)
            handler.setFormatter(log_formatter)
            app.logger.addHandler(handler)
        else:
            app.logger.handlers[0].setFormatter(log_formatter)

        # Challenge logger
        handler = logging.FileHandler(
            app.config.get('CHALLENGELOG', '/tmp/scoreboard.challenge.log'))
        handler.setLevel(logging.INFO)
        handler.setFormatter(logger.Formatter('%(asctime)s %(client)s %(message)s'))
        local_logger = logging.getLogger('scoreboard')
        local_logger.addHandler(handler)
        app.challenge_log = local_logger

        #Configure Scss to watch the files
        app.debug = app.config.get('DEBUG')
        scss_compiler = flask_scss.Scss(app, static_dir='static/css', asset_dir='static/scss')
        scss_compiler.update_scss()
    else:
        app.challenge_log = app.logger
        app.logger.handlers[0].setFormatter(log_formatter)
        logging.getLogger().handlers[0].setFormatter(log_formatter)

    # Install a default error handler
    error_titles = {
        401: 'Unauthorized',
        403: 'Forbidden',
        500: 'Internal Error',
    }

    return app


# Global app instance
app = create_app()


def api_error_handler(ex):
    """Handle errors as appropriate depending on path."""
    try:
        status_code = ex.code
    except AttributeError:
        status_code = 500
    if flask.request.path.startswith('/api/'):
        app.logger.error(str(ex))
        if app.config.get('DEBUG', False):
            resp = flask.jsonify(message=str(ex))
        else:
            resp = flask.jsonify(message='Internal Server Error')
        resp.status_code = status_code
        return resp
    return flask.make_response(
        flask.render_template(
            'error.html', exc=ex,
            title=error_titles.get(status_code, 'Error')),
        status_code)

for c in exceptions.default_exceptions.iterkeys():
    app.register_error_handler(c, api_error_handler)
