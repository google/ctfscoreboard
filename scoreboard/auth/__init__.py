"""
This supports multiple auth systems as configured by the LOGIN_METHOD setting.

The required API includes:
    login_user(flask_request): returns User or None
    get_login_uri(): returns URI for login
    get_register_uri(): returns URI for registration
    logout(): returns None
    register(flask_request): register a new user
"""


from scoreboard import config


_login_method = config.get('LOGIN_METHOD')
if _login_method == 'local':
    from scoreboard.auth.local import *
elif _login_method == 'appengine':
    from scoreboard.auth.appengine import *
else:
    raise ImportError('Unhandled LOGIN_METHOD %s' % _login_method)
