"""Appengine based login support."""


from google.appengine.api import users

from scoreboard import controllers
from scoreboard import errors
from scoreboard import models


def login_user(_):
    """Login based on GAE Auth."""
    gae_user = users.get_current_user()
    if not gae_user:
        return None
    user = models.User.get_by_email(gae_user.email())
    if not user:
        raise errors.LoginError('No user found for user %s' % gae_user.email())
    return user


def get_login_uri():
    return users.create_login_url('/')


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
    user = controllers.register_user(gae_user.email(), data['nick'], '',
            data.get('team_id'), data.get('team_name'), data.get('team_code'))
    models.commit()
    return user
