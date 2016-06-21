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

import collections
import time

import flask
from sqlalchemy import event

from scoreboard import main
from scoreboard import models
from scoreboard import utils

app = main.get_app()


DEFAULT_CSP_POLICY = {
        'default-src': ["'self'"],
        'script-src': [
            "'self'",
            "'unsafe-eval'",  # Needed for Charts.js
        ],
        'frame-ancestors': ["'none'"],
        'img-src': [
            "'self'",
            'data:',
        ],
        'object-src': ["'none'"],
        'reflected-xss': ['block'],
        'font-src': [
            "'self'",
            'fonts.gstatic.com',
        ],
        'style-src': [
            "'self'",
            'fonts.googleapis.com',
            "'unsafe-inline'",  # Needed for Charts.js
        ],
        }

_CSP_POLICY_STRING = None


def get_csp_policy():
    global _CSP_POLICY_STRING
    if _CSP_POLICY_STRING is not None:
        return _CSP_POLICY_STRING
    if app.config.get('CSP_POLICY'):
        policy = app.config.get('CSP_POLICY')
    elif app.config.get('EXTEND_CSP_POLICY'):
        policy = collections.defaultdict(list)
        for k, v in DEFAULT_CSP_POLICY.iteritems():
            policy[k] = v
        for k, v in app.config.get('EXTEND_CSP_POLICY').iteritems():
            policy[k].extend(v)
    else:
        policy = DEFAULT_CSP_POLICY
    components = []
    for k, v in policy.iteritems():
        sources = ' '.join(v)
        components.append(k + ' ' + sources)
    _CSP_POLICY_STRING = '; '.join(components)
    return _CSP_POLICY_STRING


# Setup flask.g
@app.before_request
def load_globals():
    """Prepopulate flask.g.* with properties."""
    try:
        del flask.g.user
    except AttributeError:
        pass
    try:
        del flask.g.team
    except AttributeError:
        pass
    if (app.config.get('SESSION_EXPIRATION_SECONDS') and
            flask.session.get('expires') > time.time()):
        flask.session.clear()
        return
    flask.g.uid = flask.session.get('user')
    flask.g.tid = flask.session.get('team')
    flask.g.admin = flask.session.get('admin') or False


# Add headers to responses
@app.after_request
def add_headers(response):
    """Add security-related headers to all outgoing responses."""
    h = response.headers
    h.add('Content-Security-Policy', get_csp_policy())
    h.add('X-Frame-Options', 'DENY')
    h.add('X-XSS-Protection', '1', mode='block')
    return response


@app.context_processor
def util_contexts():
    return dict(gametime=utils.GameTime)


_query_count = 0


if app.config.get('COUNT_QUERIES'):
    @event.listens_for(models.db.engine, 'before_cursor_execute')
    def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany):
        global _query_count
        _query_count += 1

    @app.after_request
    def count_queries(response):
        global _query_count
        if _query_count > 0:
            app.logger.info('Request issued %d queries.', _query_count)
            _query_count = 0
        return response


def ensure_setup():
    if not app:
        raise RuntimeError('Invalid app setup.')
