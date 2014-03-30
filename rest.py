import flask
from flask.ext import restful
from flask.ext.restful import fields

from app import app
import controllers
import errors
import models
import utils

api = restful.Api(app)


### Custom fields
class HintField(fields.Raw):
  """Custom to show hint only if unlocked or admin."""

  def format(self, value):
    if getattr(value, '__iter__', None):
      return [self.format(v) for v in value]
    res = {
        'hid': value.hid,
        'challenge_cid': value.challenge_cid,
        'cost': value.cost,
    }
    if value.is_unlocked() or (flask.g.user and flask.g.user.admin):
      res['hint'] = value.hint
    return res


### User/team management, logins, etc.
class User(restful.Resource):
  decorators = [utils.login_required]

  resource_fields = {
      'uid': fields.Integer,
      'email': fields.String,
      'nick': fields.String,
      'admin': fields.Boolean,
      'team': fields.Integer(attribute='team_tid')
  }

  @restful.marshal_with(resource_fields)
  def get(self, user_id):
    if not flask.g.user.uid == user_id and not flask.g.user.admin:
      raise errors.AccessDeniedError('No access to that user.')
    return models.User.query.get_or_404(user_id)

  @restful.marshal_with(resource_fields)
  def put(self, user_id):
    if not flask.g.user.uid == user_id and not flask.g.user.admin:
      raise errors.AccessDeniedError('No access to that user.')
    user = models.User.query.get_or_404(user_id)
    data = flask.request.get_json()
    if flask.g.user.admin and 'admin' in data:
      user.admin = utils.parse_bool(data['admin'])
    if data.get('password'):
      user.set_password(data['password'])
    models.commit()
    return user


class UserList(restful.Resource):
  resource_fields = {
      'users': fields.Nested(User.resource_fields),
  }

  @utils.admin_required
  @restful.marshal_with(resource_fields)
  def get(self):
    return dict(users=models.User.query.all())

  @restful.marshal_with(User.resource_fields)
  def post(self):
    """Register a new user."""
    if flask.g.user:
      raise errors.ValidationError('Cannot register while logged in.')
    data = flask.request.get_json()
    user = controllers.register_user(data['email'], data['nick'],
        data['password'], data.get('team_id'), data.get('team_name'),
        data.get('team_code'))
    return user


class Team(restful.Resource):
  decorators = [utils.login_required]

  team_fields = {
      'tid': fields.Integer,
      'name': fields.String,
      'score': fields.Integer,
  }
  resource_fields = team_fields.copy()
  resource_fields['players'] = fields.Nested(User.resource_fields)

  @restful.marshal_with(resource_fields)
  def get(self, team_id):
    if not utils.access_team(team_id):
      raise errors.AccessDeniedError('No access to that team.')
    team = models.Team.query.get_or_404(team_id)
    result = {}
    for k in self.team_fields:
      result[k] = getattr(team, k)
    result['players'] = list(team.players.all())
    return result


class TeamList(restful.Resource):
  resource_fields = {
      'teams': fields.Nested(Team.team_fields),
  }

  @restful.marshal_with(resource_fields)
  def get(self):
    return dict(teams=models.Team.query.all())


class Session(restful.Resource):
  """Represents a logged-in session, used for login/logout."""

  resource_fields = {
      'user': fields.Nested(User.resource_fields),
      'team': fields.Nested(Team.team_fields),
  }

  @restful.marshal_with(resource_fields)
  @utils.login_required
  def get(self):
    """Get the current session."""
    return dict(user=flask.g.user, team=flask.g.team)

  @restful.marshal_with(User.resource_fields)
  def post(self):
    """Login a user."""
    data = flask.request.get_json()
    user = controllers.user_login(data['email'], data['password'])
    if not user:
      raise errors.LoginError('Invalid username/password')
    return user

  def delete(self):
    flask.session['user'] = None
    return {'message': 'OK'}

api.add_resource(UserList, '/api/users')
api.add_resource(User, '/api/users/<int:user_id>')
api.add_resource(TeamList, '/api/teams')
api.add_resource(Team, '/api/teams/<int:team_id>')
api.add_resource(Session, '/api/session')


### Challenges
class Challenge(restful.Resource):
  decorators = [utils.admin_required]

  resource_fields = {
      'cid': fields.Integer,
      'name': fields.String,
      'points': fields.Integer,
      'description': fields.String,
      'unlocked': fields.Boolean,
      'hints': HintField,
      'cat_cid': fields.Integer,
      'answered': fields.Boolean,
      'solves': fields.Integer,
  }

  @restful.marshal_with(resource_fields)
  def get(self, challenge_id):
    return models.Challenge.query.get_or_404(challenge_id)

  @restful.marshal_with(resource_fields)
  def put(self, challenge_id):
    challenge = models.Challenge.query.get_or_404(challenge_id)
    data = flask.request.get_json()
    # TODO: updates
    return challenge


class ChallengeList(restful.Resource):
  decorators = [utils.admin_required]

  resource_fields = {
      'challenges': fields.Nested(Challenge.resource_fields)
  }

  @restful.marshal_with(resource_fields)
  def get(self):
    return dict(challenges=list(models.Challenge.query.all()))

  @restful.marshal_with(Challenge.resource_fields)
  def post(self):
    data = flask.request.get_json()
    chall = models.Challenge.create(
        data['name'],
        data['description'],
        data['points'],
        data['answer'],
        data['cat_cid'],
        utils.parse_bool(data['unlocked']))
    models.commit()
    return chall


class Category(restful.Resource):
  decorators = [utils.login_required, utils.require_gametime]

  category_fields = {
      'cid': fields.Integer,
      'name': fields.String,
      'slug': fields.String,
      'unlocked': fields.Boolean,
      'description': fields.String,
  }
  resource_fields = category_fields.copy()
  resource_fields['challenges'] = fields.Nested(Challenge.resource_fields)

  @restful.marshal_with(resource_fields)
  def get(self, category_id):
    category = models.Category.query.get_or_404(category_id)
    return self.get_challenges(category)

  @utils.admin_required
  @restful.marshal_with(resource_fields)
  def put(self, category_id):
    category = models.Category.query.get_or_404(category_id)
    # TODO: updates
    return self.get_challenges(category)

  def get_challenges(self, category):
    if flask.g.user and flask.g.user.admin:
      challenges = category.challenges
    else:
      challenges = category.challenges.filter(models.Challenge.unlocked == True)
    res = {k: getattr(category, k) for k in self.category_fields}
    res['challenges'] = list(challenges)
    return res


class CategoryList(restful.Resource):
  decorators = [utils.login_required, utils.require_gametime]

  resource_fields = {
      'categories': fields.Nested(Category.category_fields)
  }

  @restful.marshal_with(resource_fields)
  def get(self):
    return dict(categories=list(models.Category.query.all()))

  @utils.admin_required
  @restful.marshal_with(Category.category_fields)
  def post(self):
    data = flask.request.get_json()
    return models.Category.create(
        data['name'],
        data['description'])


class Hint(restful.Resource):
  decorators = [utils.login_required, utils.team_required]

  resource_fields = {
      'hid': fields.Integer,
      'challenge_cid': fields.Integer,
      'hint': fields.String,
      'cost': fields.Integer,
  }

  @restful.marshal_with(resource_fields)
  def post(self):
    """Unlock a hint."""
    data = flask.request.get_json()
    return controllers.unlock_hint(data['hid'])


class Answer(restful.Resource):
  decorators = [utils.login_required, utils.team_required]

  # TODO: get answers for admin?

  def post(self):
    data = flask.request.get_json()
    points = controllers.submit_answer(data['cid'], data['answer'])
    return dict(points=points)

api.add_resource(Category, '/api/categories/<int:category_id>')
api.add_resource(CategoryList, '/api/categories')
api.add_resource(ChallengeList, '/api/challenges')
api.add_resource(Challenge, '/api/challenges/<int:challenge_id>')
api.add_resource(Hint, '/api/unlock_hint')
api.add_resource(Answer, '/api/answers')


### Scoreboard
class APIScoreboard(restful.Resource):

  line_fields = {
      'position': fields.Integer,
      'name': fields.String,
      'score': fields.Integer,
  }
  resource_fields = {
      'scoreboard': fields.Nested(line_fields),
  }

  @restful.marshal_with(resource_fields)
  def get(self):
    return dict(scoreboard=[{'position': i, 'name': v.name, 'score': v.score}
      for i,v in models.Team.enumerate()])

api.add_resource(APIScoreboard, '/api/scoreboard')


### Public config
class Config(restful.Resource):
  def get(self):
    return dict(teams=app.config.get('TEAMS', False))

api.add_resource(Config, '/api/config')
