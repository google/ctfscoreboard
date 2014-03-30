# Custom error classes
from werkzeug import exceptions

class AccessDeniedError(exceptions.HTTPException):
  code = 403
  data = {'message': 'Forbidden'}

class ValidationError(exceptions.HTTPException):
  code = 400

  def __init__(self, msg, *args, **kwargs):
    super(ValidationError, self).__init__(*args, **kwargs)
    self.data = {'message': msg}


class InvalidAnswerError(AccessDeniedError):
  data = {'message': 'Ha ha ha... No.'}

class LoginError(AccessDeniedError):
  data = {'message': 'Invalid username/password.'}
