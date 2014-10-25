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

# Custom error classes
from werkzeug import exceptions


class _MessageException(exceptions.HTTPException):
    """Message with JSON exception."""

    default_message = 'Error'

    def __init__(self, msg=None):
        msg = msg or default_message
        super(_MessageException, self).__init__()
        self.data = {'message': msg}


class AccessDeniedError(_MessageException):
    """No access to the resource."""
    code = 403


class ValidationError(_MessageException):
    """Error during input validation."""
    code = 400


class InvalidAnswerError(AccessDeniedError):
    """Submitting the wrong answer."""
    default_message = 'Ha ha ha... No.'


class LoginError(AccessDeniedError):
    """Failing to login."""
    default_message = 'Invalid username/password.'


class ServerError(_MessageException):
    code = 500
