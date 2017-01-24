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


"""Appengine based login support."""


import flask

from google.appengine.api import users

from scoreboard import controllers
from scoreboard import errors
from scoreboard import main
from scoreboard import models
from scoreboard import utils


app = main.get_app()


def login_user(_):
    """Login based on GAE Auth."""
    gae_user = users.get_current_user()
    if not gae_user:
        return None
    user = models.User.get_by_email(gae_user.email())
    if user and flask.request:
        user.last_login_ip = flask.request.remote_addr
        models.db.session.commit()
    return user


def get_login_uri():
    return users.create_login_url('/gae_login')


def get_register_uri():
    if not users.get_current_user():
        return users.create_login_url('/register')
    return '/register'


def logout():
    pass


def register(flask_request):
    gae_user = users.get_current_user()
    if not gae_user:
        raise errors.LoginError(
                'Cannot register if not logged into AppEngine.')
    data = flask_request.get_json()
    user = controllers.register_user(
            gae_user.email(), data['nick'], '',
            data.get('team_id'), data.get('team_name'), data.get('team_code'))
    if users.is_current_user_admin():
        user.promote()
    return user


@app.route('/gae_login')
def gae_login_handler():
    user = login_user(None)
    gae_user = users.get_current_user()
    if gae_user and not user:
        app.logger.info('No user found for user %s' % gae_user.email())
        return flask.redirect('/register')
    elif not user:
        app.logger.error('No user found and not logged in.')
        return flask.redirect(get_register_uri())
    utils.session_for_user(user)
    return flask.redirect('/')
