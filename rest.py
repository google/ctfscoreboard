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

import flask
from flask.ext import restful
from flask.ext.restful import fields
import hashlib
import os

from app import app
import controllers
import errors
import models
import utils

api = restful.Api(app)


# Custom fields
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


# User/team management, logins, etc.
class User(restful.Resource):
    decorators = [utils.login_required]

    resource_fields = {
        'uid': fields.Integer,
        'email': fields.String,
        'nick': fields.String,
        'admin': fields.Boolean,
        'team_tid': fields.Integer,
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
            if data['admin']:
                user.promote()
            else:
                user.admin = False
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
                                         data['password'], data.get(
                                             'team_id'), data.get('team_name'),
                                         data.get('team_code'))
        return user


class Team(restful.Resource):
    decorators = [utils.login_required]

    team_fields = {
        'tid': fields.Integer,
        'name': fields.String,
        'score': fields.Integer,
        'solves': fields.Integer,
    }
    resource_fields = team_fields.copy()
    resource_fields['players'] = fields.Nested(User.resource_fields)

    @restful.marshal_with(resource_fields)
    def get(self, team_id):
        if not utils.access_team(team_id):
            raise errors.AccessDeniedError('No access to that team.')
        team = models.Team.query.get_or_404(team_id)
        return self._marshal_team(team)

    def _marshal_team(self, team):
        result = {}
        for k in self.team_fields:
            result[k] = getattr(team, k)
        result['players'] = list(team.players.all())
        return result

    @restful.marshal_with(resource_fields)
    def put(self, team_id):
        if not utils.access_team(team_id):
            raise errors.AccessDeniedError('No access to that team.')
        team = models.Team.query.get_or_404(team_id)
        data = flask.request.get_json()
        # Writable fields
        for field in ('name', 'score'):
            setattr(team, field, data.get(field, getattr(team, field)))
        return self._marshal_team(team)


class TeamList(restful.Resource):
    resource_fields = {
        'teams': fields.Nested(Team.team_fields),
    }

    @restful.marshal_with(resource_fields)
    def get(self):
        return dict(teams=models.Team.query.all())


class Session(restful.Resource):

    """Represents a logged-in session, used for login/logout."""

    team_fields = Team.team_fields.copy()
    team_fields['code'] = fields.String
    resource_fields = {
        'user': fields.Nested(User.resource_fields),
        'team': fields.Nested(team_fields),
    }

    @restful.marshal_with(resource_fields)
    @utils.login_required
    def get(self):
        """Get the current session."""
        return dict(
                user=flask.g.user,
                team=flask.g.team)

    @restful.marshal_with(resource_fields)
    def post(self):
        """Login a user."""
        data = flask.request.get_json()
        user = controllers.user_login(data['email'], data['password'])
        if not user:
            raise errors.LoginError('Invalid username/password')
        return dict(user=user, team=user.team)

    def delete(self):
        flask.session['user'] = None
        return {'message': 'OK'}

api.add_resource(UserList, '/api/users')
api.add_resource(User, '/api/users/<int:user_id>')
api.add_resource(TeamList, '/api/teams')
api.add_resource(Team, '/api/teams/<int:team_id>')
api.add_resource(Session, '/api/session')


# Challenges
class Challenge(restful.Resource):
    decorators = [utils.admin_required]

    challenge_fields = {
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
    attachment_fields = {
        'aid': fields.String,
        'filename': fields.String,
    }
    resource_fields = challenge_fields.copy()
    resource_fields['attachments'] = fields.List(
            fields.Nested(attachment_fields))

    @restful.marshal_with(resource_fields)
    def get(self, challenge_id):
        return models.Challenge.query.get_or_404(challenge_id)

    @restful.marshal_with(resource_fields)
    def put(self, challenge_id):
        challenge = models.Challenge.query.get_or_404(challenge_id)
        data = flask.request.get_json()
        for field in ('name', 'description', 'points', 'cat_cid', 'unlocked'):
            setattr(
                challenge, field, data.get(field, getattr(challenge, field)))
        if 'answer' in data and data['answer']:
            challenge.change_answer(data['answer'])
        if 'hints' in data:
            challenge.set_hints(data['hints'])
        if 'attachments' in data:
            challenge.set_attachments(data['attachments'])

        models.commit()
        return challenge

    def delete(self, challenge_id):
        challenge = models.Challenge.query.get_or_404(challenge_id)
        models.db.session.delete(challenge)
        models.commit()


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
            data.get('unlocked', False))
        if 'hints' in data:
            chall.set_hints(data['hints'])
        if 'attachments' in data:
            chall.set_attachments(data['attachments'])
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
            unlocked_identity = True
            challenges = category.challenges.filter(
                models.Challenge.unlocked == unlocked_identity)
        res = {k: getattr(category, k) for k in self.category_fields}
        res['challenges'] = list(challenges)
        return res

    @utils.admin_required
    def delete(self, category_id):
        category = models.Category.query.get_or_404(category_id)
        models.db.session.delete(category)
        models.commit()


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


# Scoreboard
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
        return dict(scoreboard=[
            {'position': i, 'name': v.name, 'score': v.score}
            for i, v in models.Team.enumerate()])

api.add_resource(APIScoreboard, '/api/scoreboard')


# Public config
class Config(restful.Resource):

    def get(self):
        return dict(teams=app.config.get('TEAMS', False))

api.add_resource(Config, '/api/config')


# File upload
class Upload(restful.Resource):
    decorators = [utils.admin_required]

    def post(self):
        fp = flask.request.files['file']
        # Hash the file
        md = hashlib.sha256()
        while True:
            blk = fp.read(2**16)
            if not blk:
                break
            md.update(blk)
        fhash = md.hexdigest()
        fp.seek(0, os.SEEK_SET)
        dest_name = os.path.join(utils.attachment_dir(create=True), fhash)
        fp.save(dest_name, buffer_size=2**16)
        return dict(aid=fhash, content_type=fp.mimetype)

api.add_resource(Upload, '/api/upload')


# Admin Backup and restore
class BackupRestore(restful.Resource):
    decorators = [utils.admin_required]

    def get(self):
        categories = {}
        for cat in models.Category.query.all():
            challenges = []
            for q in cat.challenges:
                hints = []
                for h in q.hints:
                    hints.append({
                        'hint': h.hint,
                        'cost': h.cost,
                    })
                challenges.append({
                    'category': cat.cid,
                    'name': q.name,
                    'description': q.description,
                    'points': q.points,
                    'answer_hash': q.answer_hash,
                    'hints': hints,
                })
            categories[cat.cid] = {
                'name': cat.name,
                'description': cat.description,
                'challenges': challenges,
            }
        return (
            {'categories': categories},
            200,
            {'Content-Disposition': 'attachment; filename=challenges.json'})

        def post(self):
            data = flask.request.get_json()
            categories = data['categories']

            if data.get('replace', False):
                models.Hint.query.delete()
                models.Challenge.query.delete()
                models.Category.query.delete()

            cats = {}
            challs = 0
            for catid, cat in categories.iteritems():
                newcat = models.Category()
                for f in ('name', 'description'):
                    setattr(newcat, f, cat[f])
                models.db.session.add(newcat)
                cats[int(catid)] = newcat

                for challenge in cat['challenges']:
                    newchall = models.Challenge()
                    for f in ('name', 'description', 'points', 'answer_hash'):
                        setattr(newchall, f, challenge[f])
                    newchall.category = newcat
                    models.db.session.add(newchall)
                    challs += 1
                    for h in challenge.get('hints', []):
                        hint = models.Hint()
                        hint.challenge = newchall
                        hint.hint = h['hint']
                        hint.cost = int(h['cost'])
                        models.db.session.add(hint)

            models.commit()
            return {'message': '%d Categories and %d Challenges imported.' %
                    (len(cats), challs)}

api.add_resource(BackupRestore, '/api/backup')
