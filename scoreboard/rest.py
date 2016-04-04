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

import datetime
import flask
from flask.ext import restful
from flask.ext.restful import fields
import hashlib
import json
import os
import pytz

from scoreboard.app import app
from scoreboard import attachments
from scoreboard import auth
from scoreboard import cache
from scoreboard import controllers
from scoreboard import context
from scoreboard import csrfutil
from scoreboard import errors
from scoreboard import models
from scoreboard import utils

api = restful.Api(app)
context.ensure_setup()


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


class ISO8601DateTime(fields.Raw):
    """Show datetimes as ISO8601."""

    def format(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            value = datetime.fromtimestamp(value)
        if isinstance(value, (datetime.datetime, datetime.date)):
            if getattr(value, 'tzinfo', True) is None:
                value = value.replace(tzinfo=pytz.UTC)
            return value.isoformat()
        raise ValueError('Unable to convert %s to ISO8601.' % str(type(value)))


class PrerequisiteField(fields.Raw):
    """Prerequisite data."""

    def format(self, value):
        try:
            data = json.loads(value)
        except ValueError:
            return {'type': 'None'}
        return data



### Utility functions
@api.representation('application/json')
def output_json(data, code, headers=None):
    """Custom JSON output with JSONP buster."""

    settings = {}
    if app.debug:
        settings['indent'] = 4
        settings['sort_keys'] = True

    dumped = json.dumps(data, **settings)
    if not (headers and headers.pop('X-No-XSSI', None)):
        dumped = ")]}',\n" + dumped + "\n"

    resp = flask.make_response(dumped, code)
    resp.headers.extend(headers or {})
    return resp


def get_field(name, *args):
    data = flask.request.get_json()
    try:
        return data[name]
    except KeyError:
        if args:
            return args[0]
        raise errors.ValidationError(
            'Required field {} not given.'.format(name))


class User(restful.Resource):
    """Wrap User model."""

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
        promoting = False
        if utils.is_admin() and 'admin' in data:
            if data['admin'] and not user.admin:
                user.promote()
                promoting = True
            else:
                user.admin = False
        if data.get('password'):
            user.set_password(data['password'])
        if utils.is_admin():
            user.nick = data['nick']
            if not app.config.get('TEAMS', False):
                user.team.name = data['nick']
        try:
            models.commit()
        except AssertionError:
            if promoting:
                raise errors.ValidationError(
                        'Error promoting. Has player solved challenges?')
            raise
        return user


class UserList(restful.Resource):
    """Registration and listing of users."""

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
        if not data.get('nick', ''):
            raise errors.ValidationError('Need a player nick.')
        if (app.config.get('TEAMS') and not data.get('team_name', '') and not
            data.get('team_id', 0)):
            raise errors.ValidationError('Need a team name.')
        user = auth.register(flask.request)
        flask.session['user'] = user.uid
        return user


class Team(restful.Resource):
    """Manage single team."""

    decorators = [utils.login_required]

    history_fields = {
        'when': ISO8601DateTime(),
        'score': fields.Integer,
    }
    team_fields = {
        'tid': fields.Integer,
        'name': fields.String,
        'score': fields.Integer,
        'solves': fields.Integer,
    }
    solved_challenges = {
        'cid': fields.Integer,
        'name': fields.String,
        'cat_id': fields.Integer,
        'cat_name': fields.String,
        'solved': ISO8601DateTime(),
        'points': fields.Integer,
    }
    resource_fields = team_fields.copy()
    resource_fields['players'] = fields.Nested(User.resource_fields)
    resource_fields['score_history'] = fields.Nested(history_fields)
    resource_fields['solved_challenges'] = fields.Nested(solved_challenges)

    @cache.rest_team_cache('team/%d')
    @restful.marshal_with(resource_fields)
    def get(self, team_id):
        team = models.Team.query.get_or_404(team_id)
        return self._marshal_team(team, extended=True)

    def _marshal_team(self, team, extended=False):
        result = {}
        for k in self.team_fields:
            result[k] = getattr(team, k)
        if extended:
            challenges = []
            for answer in team.answers:
                challenges.append({
                    'solved': answer.timestamp,
                    'points': answer.challenge.points,
                    'name': answer.challenge.name,
                    'cid': answer.challenge_cid,
                    'cat_id': answer.challenge.category.cid,
                    'cat_name': answer.challenge.category.name,
                    })
            result['solved_challenges'] = challenges
            result['score_history'] = team.score_history
        else:
            result['solved_challenges'] = []
            result['score_history'] = []
        if utils.access_team(team.tid):
            result['players'] = list(team.players.all())
        else:
            result['players'] = []
        return result

    @utils.admin_required
    @restful.marshal_with(resource_fields)
    def put(self, team_id):
        if not utils.access_team(team_id):
            raise errors.AccessDeniedError('No access to that team.')
        team = models.Team.query.get_or_404(team_id)
        app.logger.info('Update of team %r by %r.', team, flask.g.user)
        data = flask.request.get_json()
        # Writable fields
        for field in ('name', 'score'):
            setattr(team, field, data.get(field, getattr(team, field)))
        models.commit()
        cache.delete_team('team/%d')
        return self._marshal_team(team)


class TeamList(restful.Resource):
    """Get a list of all teams."""

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
        'redirect': fields.String,
    }

    @restful.marshal_with(resource_fields)
    @utils.login_required
    def get(self):
        """Get the current session."""
        return dict(
                user=getattr(flask.g, 'user', None),
                team=getattr(flask.g, 'team', None))

    @restful.marshal_with(resource_fields)
    def post(self):
        """Login a user."""
        user = auth.login_user(flask.request)
        if not user:
            redir = auth.get_login_uri()
            if redir:
                return dict(redirect=redir)
            return {}
        app.logger.info('%r logged in.', user)
        flask.session['user'] = user.uid
        return dict(user=user, team=user.team)

    def delete(self):
        auth.logout()
        if flask.session.get('user', None):
            del flask.session['user']
            app.logger.info('%r logging out.', flask.g.user)
        flask.g.user = None
        flask.g.team = None
        return {'message': 'OK'}


class PasswordReset(restful.Resource):
    """Setup for password reset."""

    def get(self, email):
        """Send a password reset email."""
        user = models.User.get_by_email(email)
        if not user:
            flask.abort(404)
        controllers.offer_password_reset(user)
        app.logger.info('Request password reset for %r.', user)
        return {'message': 'Reset email sent.'}

    def post(self, email):
        """Verify reset and set new password."""
        # TODO: Move to controller
        data = flask.request.get_json()
        user = models.User.get_by_email(email)
        if not user:
            flask.abort(404)
        if not user.verify_token(data.get('token', '')):
            raise errors.AccessDeniedError('Invalid token.')
        if data['password'] != data['password2']:
            raise errors.ValidationError("Passwords don't match.")
        user.set_password(data['password'])
        app.logger.info('Password reset for %r.', user)
        models.commit()
        controllers.user_login(email, data['password'])
        return {'message': 'Password reset.'}

api.add_resource(UserList, '/api/users')
api.add_resource(User, '/api/users/<int:user_id>')
api.add_resource(TeamList, '/api/teams')
api.add_resource(Team, '/api/teams/<int:team_id>')
api.add_resource(Session, '/api/session')
api.add_resource(PasswordReset, '/api/pwreset/<email>')


class Challenge(restful.Resource):
    """A single challenge."""

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
        'weight': fields.Integer,
        'prerequisite': PrerequisiteField,
        'teaser': fields.Boolean,
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
        old_unlocked = challenge.unlocked
        for field in (
                'name', 'description', 'points', 'cat_cid', 'unlocked', 'weight'):
            setattr(
                challenge, field, data.get(field, getattr(challenge, field)))
        if 'answer' in data and data['answer']:
            challenge.change_answer(data['answer'])
        if 'hints' in data:
            challenge.set_hints(data['hints'])
        if 'attachments' in data:
            challenge.set_attachments(data['attachments'])
        if 'prerequisite' in data:
            challenge.set_prerequisite(data['prerequisite'])
        else:
            challenge.prerequisite = ''
        if challenge.unlocked and not old_unlocked:
            news = 'Challenge "%s" unlocked!' % challenge.name
            models.News.game_broadcast(message=news)

        app.logger.info('Challenge %s updated by %r.', challenge, flask.g.user)

        models.commit()
        cache.clear()
        return challenge

    def delete(self, challenge_id):
        challenge = models.Challenge.query.get_or_404(challenge_id)
        models.db.session.delete(challenge)
        models.commit()
        cache.clear()


class ChallengeList(restful.Resource):
    """Create & manage challenges for admins."""

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
        unlocked = data.get('unlocked', False)
        chall = models.Challenge.create(
            data['name'],
            data['description'],
            data['points'],
            data['answer'],
            data['cat_cid'],
            unlocked)
        if 'hints' in data:
            chall.set_hints(data['hints'])
        if 'attachments' in data:
            chall.set_attachments(data['attachments'])
        if 'prerequisite' in data:
            chall.set_prerequisite(data['prerequisite'])

        if unlocked:
            news = 'New challenge created: "%s"' % chall.name
            models.News.game_broadcast(message=news)

        models.commit()
        app.logger.info('Challenge %s created by %r.', chall, flask.g.user)
        return chall


class Category(restful.Resource):
    """Single category of challenges."""

    decorators = [utils.login_required, utils.require_gametime]

    category_fields = {
        'cid': fields.Integer,
        'name': fields.String,
        'slug': fields.String,
        'unlocked': fields.Boolean,
        'description': fields.String,
        'challenge_count': fields.Integer,
        'solved_count': fields.Integer,
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
        category.name = get_field('name')
        category.description = get_field('description', '')

        app.logger.info('Category %s updated by %r.', category, flask.g.user)
        models.commit()
        cache.clear()
        return self.get_challenges(category)

    @classmethod
    def get_challenges(cls, category):
        if flask.g.user and flask.g.user.admin:
            challenges = category.challenges
        else:
            raw = category.get_challenges()
            challenges = []
            for ch in raw:
                if ch.unlocked_for_team(flask.g.team):
                    challenges.append(ch)
                elif ch.teaser:
                    challenges.append(cls._tease_challenge(ch))
        res = {k: getattr(category, k) for k in cls.category_fields}
        res['challenges'] = list(challenges)
        return res

    @staticmethod
    def _tease_challenge(chall):
        res = {k: getattr(chall, k) for k in Challenge.resource_fields}
        for f in ('description', 'hints', 'attachments'):
            del res[f]
        return res

    @utils.admin_required
    def delete(self, category_id):
        category = models.Category.query.get_or_404(category_id)
        models.db.session.delete(category)
        cache.clear()
        models.commit()


class CategoryList(restful.Resource):
    """List of all categories."""

    decorators = [utils.login_required, utils.require_gametime]

    resource_fields = {
        'categories': fields.Nested(Category.resource_fields)
    }

    @cache.rest_team_cache('cats/%d')
    @restful.marshal_with(resource_fields)
    def get(self):
        q = models.Category.joined_query()
        categories = [Category.get_challenges(c) for c in q.all()]
        return dict(categories=categories)

    @utils.admin_required
    @restful.marshal_with(Category.category_fields)
    def post(self):
        cat = models.Category.create(
            get_field('name'),
            get_field('description', ''))
        models.commit()
        app.logger.info('Category %s created by %r.', cat, flask.g.user)
        cache.clear()
        return cat


class Hint(restful.Resource):
    """Wrap hint just for unlocking."""

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
        hint = controllers.unlock_hint(data['hid'])
        app.logger.info('Hint %s unlocked by %r.', hint, flask.g.user)
        models.commit()
        cache.delete_team('cats/%d')
        return hint


class Answer(restful.Resource):
    """Submit an answer."""

    decorators = [utils.login_required, utils.team_required]

    # TODO: get answers for admin?

    def post(self):
        data = flask.request.get_json()
        points = controllers.submit_answer(data['cid'], data['answer'])
        models.commit()
        cache.delete_team('cats/%d')
        cache.delete('scoreboard')
        return dict(points=points)

api.add_resource(Category, '/api/categories/<int:category_id>')
api.add_resource(CategoryList, '/api/categories')
api.add_resource(ChallengeList, '/api/challenges')
api.add_resource(Challenge, '/api/challenges/<int:challenge_id>')
api.add_resource(Hint, '/api/unlock_hint')
api.add_resource(Answer, '/api/answers')


class APIScoreboard(restful.Resource):
    """Retrieve the scoreboard."""

    line_fields = {
        'position': fields.Integer,
        'tid': fields.Integer,
        'name': fields.String,
        'score': fields.Integer,
        'history': fields.Nested(Team.history_fields),
    }
    resource_fields = {
        'scoreboard': fields.Nested(line_fields),
    }

    @cache.rest_cache('scoreboard')
    @restful.marshal_with(resource_fields)
    def get(self):
        return dict(scoreboard=[
            {'position': i, 'name': v.name, 'tid': v.tid,
             'score': v.score, 'history': v.score_history}
            for i, v in models.Team.enumerate(with_history=True)])

api.add_resource(APIScoreboard, '/api/scoreboard')


class Config(restful.Resource):
    """Get basic config for the scoreboard.

    This should not change often as it is highly-cached on the client.
    """

    def get(self):
        datefmt = ISO8601DateTime()
        return dict(
            teams=app.config.get('TEAMS', False),
            sbname=app.config.get('TITLE', 'Scoreboard'),
            news_mechanism='poll',
            news_poll_interval=app.config.get('NEWS_POLL_INTERVAL', 60000),
            csrf_token=csrfutil.get_csrf_token(),
            rules=app.config.get('RULES', '/rules'),
            game_start=datefmt.format(utils.GameTime.start),
            game_end=datefmt.format(utils.GameTime.end),
            login_url=auth.get_login_uri(),
            register_url=auth.get_register_uri(),
            login_method=app.config.get('LOGIN_METHOD', 'local'),
            )

api.add_resource(Config, '/api/config')


class News(restful.Resource):
    """Display and manage news."""

    resource_fields = {
        'nid': fields.Integer,
        'news_type': fields.String,
        'timestamp': ISO8601DateTime,
        'author': fields.String,
        'message': fields.String,
    }

    @restful.marshal_with(resource_fields)
    def get(self):
        if flask.g.team:
            news = models.News.for_team(flask.g.team)
        else:
            news = models.News.for_public()
        return list(news)

    @utils.admin_required
    @restful.marshal_with(resource_fields)
    def post(self):
        data = flask.request.get_json()
        tid = None
        if 'tid' in data:
            try:
                tid = int(data['tid'])
            except ValueError:
                pass
        author = flask.g.user.nick
        if tid:
            item = models.News.unicast(tid, author, data['message'])
        else:
            item = models.News.broadcast(author, data['message'])
        models.commit()
        return item


api.add_resource(News, '/api/news')


class Page(restful.Resource):
    """Create and retrieve static pages."""

    resource_fields = {
        'path': fields.String,
        'title': fields.String,
        'contents': fields.String,
    }

    @restful.marshal_with(resource_fields)
    def get(self, path):
        app.logger.info('Path: %s', path)
        return models.Page.query.get_or_404(path)

    @utils.admin_required
    @restful.marshal_with(resource_fields)
    def post(self, path):
        data = flask.request.get_json()
        page = models.Page.query.get(path)
        if not page:
            page = models.Page()
            page.path = path
            models.db.session.add(page)
        page.title = data.get('title', '')
        page.contents = data.get('contents', '')
        models.commit()
        return page

    @utils.admin_required
    def delete(self, path):
        page = models.Page.query.get_or_404(path)
        models.db.session.delete(page)
        models.commit()
        return {}

api.add_resource(Page, '/api/page/<path:path>')


class Upload(restful.Resource):
    """Allow uploading of files."""

    decorators = [utils.admin_required]

    def post(self):
        fp = flask.request.files['file']
        aid, fpath = attachments.upload(fp)
        return dict(aid=aid, fpath=fpath, content_type=fp.mimetype)

api.add_resource(Upload, '/api/upload')


class BackupRestore(restful.Resource):
    """Control for backup and restore."""
    decorators = [utils.admin_required]

    def get(self):
        # TODO: refactor, this is messy
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
                attachments = []
                for a in q.attachments:
                    attachments.append({
                        'aid': a.aid,
                        'filename': a.filename,
                        'content_type': a.content_type,
                    })
                challenges.append({
                    'cid': q.cid,
                    'category': cat.cid,
                    'name': q.name,
                    'description': q.description,
                    'points': q.points,
                    'answer_hash': q.answer_hash,
                    'hints': hints,
                    'attachments': attachments,
                    'prerequisite': q.prerequisite,
                    'weight': q.weight,
                })
            categories[cat.cid] = {
                'name': cat.name,
                'description': cat.description,
                'challenges': challenges,
                'slug': cat.slug,
            }
        return (
            {'categories': categories},
            200,
            {'Content-Disposition': 'attachment; filename=challenges.json'})

    def post(self):
        # TODO: refactor, this is messy
        data = flask.request.get_json()
        categories = data['categories']

        if data.get('replace', False):
            models.Attachment.query.delete()
            models.Hint.query.delete()
            models.Challenge.query.delete()
            models.Category.query.delete()

        cats = {}
        challs = 0
        for catid, cat in categories.iteritems():
            newcat = models.Category()
            for f in ('name', 'description', 'slug'):
                setattr(newcat, f, cat[f])
            models.db.session.add(newcat)
            cats[int(catid)] = newcat

            for challenge in cat['challenges']:
                newchall = models.Challenge()
                for f in ('cid', 'name', 'description', 'points', 'answer_hash',
                          'prerequisite', 'weight'):
                    setattr(newchall, f, challenge.get(f, None))
                newchall.category = newcat
                models.db.session.add(newchall)
                challs += 1
                for h in challenge.get('hints', []):
                    hint = models.Hint()
                    hint.challenge = newchall
                    hint.hint = h['hint']
                    hint.cost = int(h['cost'])
                    models.db.session.add(hint)
                for a in challenge.get('attachments', []):
                    attachment = models.Attachment()
                    attachment.challenge = newchall
                    attachment.aid = a['aid']
                    attachment.filename = a['filename']
                    attachment.content_type = a['content_type']
                    models.db.session.add(attachment)

        models.commit()
        cache.clear()
        return {'message': '%d Categories and %d Challenges imported.' %
                (len(cats), challs)}

api.add_resource(BackupRestore, '/api/backup')


class CTFTimeScoreFeed(restful.Resource):
    """Provide a JSON feed to CTFTime.

    At this time, it is only intended to cover the manditory fields in the
    feed: https://ctftime.org/json-scoreboard-feed
    """
    
    def get(self):
        standings = [{'pos': i, 'team': v.name, 'score': v.score}
                for i, v in models.Team.enumerate()]
        data = {'standings': standings} 
        return data, 200, {'X-No-XSSI': 1}

api.add_resource(CTFTimeScoreFeed, '/api/ctftime/scoreboard')
