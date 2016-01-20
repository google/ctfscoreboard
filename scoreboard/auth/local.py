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
    models.commit()
    return user
