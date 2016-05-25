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


"""Local login support."""

from scoreboard import controllers
from scoreboard import errors
from scoreboard import models


def login_user(flask_request):
    """Get the user for this request."""
    data = flask_request.get_json()
    user = models.User.login_user(data['email'], data['password'])
    if not user:
        raise errors.LoginError('Invalid username/password.')
    return user


def get_login_uri():
    return '/login'


def get_register_uri():
    return '/register'


def logout():
    pass


def register(flask_request):
    data = flask_request.get_json()
    user = controllers.register_user(data['email'], data['nick'],
            data['password'], data.get('team_id'), data.get('team_name'),
            data.get('team_code'))
    return user
