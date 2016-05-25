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


"""
This supports multiple auth systems as configured by the LOGIN_METHOD setting.

The required API includes:
    login_user(flask_request): returns User or None
    get_login_uri(): returns URI for login
    get_register_uri(): returns URI for registration
    logout(): returns None
    register(flask_request): register a new user
"""


from scoreboard import app


_login_method = app.config.get('LOGIN_METHOD')
if _login_method == 'local':
    from scoreboard.auth.local import *
elif _login_method == 'appengine':
    from scoreboard.auth.appengine import *
else:
    raise ImportError('Unhandled LOGIN_METHOD %s' % _login_method)
