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

from scoreboard.app import app
from scoreboard import models
from scoreboard import utils

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


# Add headers to responses
@app.after_request
def add_headers(response):
    h = response.headers
    # TODO: CSP
    h.add('X-Frame-Options', 'DENY')
    h.add('X-XSS-Protection', '1', mode='block')
    return response


@app.context_processor
def util_contexts():
    return dict(gametime=utils.GameTime)


def ensure_setup():
    if not app:
        raise RuntimeError('Invalid app setup.')
