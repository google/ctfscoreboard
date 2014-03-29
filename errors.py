# Custom error classes
from werkzeug import exceptions

class AccessDeniedError(exceptions.HTTPException):
  code = 403

class ValidationError(exceptions.HTTPException):
  code = 400

class InvalidAnswerError(AccessDeniedError):
  pass

class LoginError(AccessDeniedError):
  pass
