from flask.ext import restful

from app import app
import errors
import models
import utils

api = restful.Api(app)


### User management
class User(restful.Resource):
  def get(self, user_id):
    pass

  def put(self, user_id):
    pass


class UserList(restful.Resource):
  @utils.admin_required
  def get(self):
    pass

  # Registration/user creation
  def post(self):
    pass

api.add_resource(UserList, '/users')
api.add_resource(User, '/users/<int:user_id>')
