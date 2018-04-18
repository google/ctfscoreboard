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

import datetime
import flask
import flask_restful
from flask_restful import fields
import json
import pytz

from scoreboard import attachments
from scoreboard import auth
from scoreboard import cache
from scoreboard import controllers
from scoreboard import context
from scoreboard import csrfutil
from scoreboard import errors
from scoreboard import main
from scoreboard import models
from scoreboard import utils
from scoreboard import validators

app = main.get_app()
api = flask_restful.Api(app)
context.ensure_setup()


# Custom fields
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


# Utility functions
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


class User(flask_restful.Resource):
    """Wrap User model."""

    decorators = [utils.login_required]

    resource_fields = {
        'uid': fields.Integer,
        'email': fields.String,
        'nick': fields.String,
        'admin': fields.Boolean,
        'team_tid': fields.Integer,
    }

    @flask_restful.marshal_with(resource_fields)
    def get(self, user_id):
        if not flask.g.uid == user_id and not flask.g.admin:
            raise errors.AccessDeniedError('No access to that user.')
        return models.User.query.get_or_404(user_id)

    @flask_restful.marshal_with(resource_fields)
    def put(self, user_id):
        if not flask.g.uid == user_id and not flask.g.admin:
            raise errors.AccessDeniedError('No access to that user.')
        user = models.User.query.get_or_404(user_id)
        data = flask.request.get_json()
        if utils.is_admin() and 'admin' in data:
            if data['admin'] and not user.admin:
                try:
                    user.promote()
                except AssertionError:
                    raise errors.ValidationError(
                        'Error promoting. Has player solved challenges?')
            else:
                user.admin = False
        if data.get('password'):
            user.set_password(data['password'])
        if utils.is_admin():
            user.nick = data['nick']
            if not app.config.get('TEAMS') and user.team:
                user.team.name = data['nick']

        try:
            models.commit()
        except AssertionError:
                raise errors.ValidationError(
                        'Error in updating user.  Details are logged.')
        return user


class UserList(flask_restful.Resource):
    """Registration and listing of users."""

    resource_fields = {
        'users': fields.Nested(User.resource_fields),
    }

    @utils.admin_required
    @flask_restful.marshal_with(resource_fields)
    def get(self):
        return dict(users=models.User.all())

    @flask_restful.marshal_with(User.resource_fields)
    def post(self):
        """Register a new user."""
        if utils.is_logged_in():
            raise errors.ValidationError('Cannot register while logged in.')
        data = flask.request.get_json()
        if not data.get('nick', ''):
            raise errors.ValidationError('Need a player nick.')
        if (app.config.get('TEAMS') and
                not data.get('team_name', '') and
                not data.get('team_id', 0)):
            app.logger.warning('User attempted to register without team.')
            raise errors.ValidationError('Need a team name.')
        if (app.config.get('INVITE_KEY') and
                data.get('invite_key', '').strip() !=
                app.config.get('INVITE_KEY')):
            app.logger.warning(
                    'Attempted invite-only registration with invalid '
                    'invite key: %s', data.get('invite_key', ''))
            raise errors.ValidationError('Invalid invite key!')
        app.logger.debug('Passed registration validation for new user.')
        user = auth.register(flask.request)
        utils.session_for_user(user)
        return user


class Team(flask_restful.Resource):
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
        'solved': ISO8601DateTime(),
        'points': fields.Integer,
    }
    resource_fields = team_fields.copy()
    resource_fields['players'] = fields.Nested(User.resource_fields)
    resource_fields['score_history'] = fields.Nested(history_fields)
    resource_fields['solved_challenges'] = fields.Nested(solved_challenges)

    @flask_restful.marshal_with(resource_fields)
    def get(self, team_id):
        # TODO: this takes too many queries, fix to 1
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
                    'points': answer.current_points,
                    'name': answer.challenge.name,
                    'cid': answer.challenge_cid,
                    })
            result['solved_challenges'] = challenges
            result['score_history'] = team.score_history
        else:
            result['solved_challenges'] = []
            result['score_history'] = []
        if team.can_access():
            result['players'] = list(team.players.all())
        else:
            result['players'] = []
        return result

    @utils.admin_required
    @flask_restful.marshal_with(resource_fields)
    def put(self, team_id):
        team = models.Team.query.get_or_404(team_id)
        app.logger.info('Update of team %r by %r.',
                        team, models.User.current())
        data = flask.request.get_json()
        # Writable fields
        for field in ('name', 'score'):
            setattr(team, field, data.get(field, getattr(team, field)))
        models.commit()
        cache.delete_team('team/%d')
        return self._marshal_team(team)


class TeamList(flask_restful.Resource):
    """Get a list of all teams."""

    resource_fields = {
        'teams': fields.Nested(Team.team_fields),
    }

    @flask_restful.marshal_with(resource_fields)
    def get(self):
        return dict(teams=models.Team.all())


class TeamChange(flask_restful.Resource):
    """Endpoint for changing teams."""

    resource_fields = {
        'uid': fields.Integer,
        'team_tid': fields.Integer,
        'code': fields.String,
    }

    @utils.login_required
    @flask_restful.marshal_with(resource_fields)
    def put(self):
        current = models.User.current()
        if not (current.admin or current.uid == get_field('uid')):
            raise errors.AccessDeniedError('Cannot Modify this User')
        controllers.change_user_team(
                get_field('uid'), get_field('team_tid'), get_field('code'))


class Session(flask_restful.Resource):

    """Represents a logged-in session, used for login/logout."""

    team_fields = {
        'tid': fields.Integer,
        'name': fields.String,
        'score': fields.Integer,
        'code': fields.String,
    }
    resource_fields = {
        'user': fields.Nested(User.resource_fields),
        'team': fields.Nested(team_fields),
        'redirect': fields.String,
    }

    @utils.login_required
    @flask_restful.marshal_with(resource_fields)
    def get(self):
        """Get the current session."""
        return dict(
                user=models.User.current(),
                team=models.Team.current())

    @flask_restful.marshal_with(resource_fields)
    def post(self):
        """Login a user."""
        user = auth.login_user(flask.request)
        if not user:
            redir = auth.get_login_uri()
            if redir:
                return dict(redirect=redir)
            return {}
        app.logger.info('%r logged in.', user)
        utils.session_for_user(user)
        return dict(user=user, team=user.team)

    def delete(self):
        auth.logout()
        if flask.session.get('user', None):
            app.logger.info('%r logging out.', models.User.current())
            flask.session.clear()
        try:
            del flask.g.user
        except:  # noqa: E722
            pass
        try:
            del flask.g.team
        except:  # noqa: E722
            pass
        return {'message': 'OK'}


class PasswordReset(flask_restful.Resource):
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
        token = data.get('token', '')
        try:
            user.verify_token(token)
        except errors.ValidationError as ex:
            app.logger.warning('Error validating password reset: %s', str(ex))
            raise
        except Exception as ex:
            app.logger.exception(
                    'Unhandled exception during password reset: %s', str(ex))
            raise
        if data['password'] != data['password2']:
            raise errors.ValidationError("Passwords don't match.")
        user.set_password(data['password'])
        app.logger.info('Password reset for %r.', user)
        models.commit()
        utils.session_for_user(user)
        return {'message': 'Password reset.'}


api.add_resource(UserList, '/api/users')
api.add_resource(User, '/api/users/<int:user_id>')
api.add_resource(TeamChange, '/api/teams/change')
api.add_resource(TeamList, '/api/teams')
api.add_resource(Team, '/api/teams/<int:team_id>')
api.add_resource(Session, '/api/session')

if app.config.get('LOGIN_METHOD') == 'local':
    api.add_resource(PasswordReset, '/api/pwreset/<email>')


class Challenge(flask_restful.Resource):
    """A single challenge."""

    decorators = [utils.admin_required]

    challenge_fields = {
        'cid': fields.Integer,
        'name': fields.String,
        'points': fields.Integer,
        'description': fields.String,
        'unlocked': fields.Boolean,
        'answered': fields.Boolean,
        'solves': fields.Integer,
        'weight': fields.Integer,
        'prerequisite': PrerequisiteField,
        'teaser': fields.Boolean,
        'validator': fields.String,
    }
    attachment_fields = {
        'aid': fields.String,
        'filename': fields.String,
    }
    tags_fields = {
        'tagslug': fields.String,
        'name':    fields.String,
    }
    team_fields = {
        'name': fields.String,
        'tid': fields.Integer,
    }
    answers_fields = {
        'timestamp': fields.DateTime,
    }
    answers_fields['team'] = fields.Nested(team_fields)

    resource_fields = challenge_fields.copy()
    resource_fields['attachments'] = fields.List(
            fields.Nested(attachment_fields))
    resource_fields['tags'] = fields.List(
            fields.Nested(tags_fields))
    resource_fields['answers'] = fields.List(
            fields.Nested(answers_fields))

    @flask_restful.marshal_with(resource_fields)
    def get(self, challenge_id):
        return models.Challenge.query.get_or_404(challenge_id)

    @flask_restful.marshal_with(resource_fields)
    def put(self, challenge_id):
        challenge = models.Challenge.query.get_or_404(challenge_id)
        data = flask.request.get_json()
        old_unlocked = challenge.unlocked
        for field in (
                'name', 'description', 'points',
                'unlocked', 'weight'):
            setattr(
                challenge, field, data.get(field, getattr(challenge, field)))
        if 'validator' in data:
            if not validators.IsValidator(data['validator']):
                raise errors.ValidationError('Invalid validator.')
            challenge.validator = data['validator']
        if 'answer' in data and data['answer']:
            answer = utils.normalize_input(data['answer'])
            validator = validators.GetValidatorForChallenge(challenge)
            validator.change_answer(answer)
        if 'attachments' in data:
            challenge.set_attachments(data['attachments'])
        if 'prerequisite' in data:
            challenge.set_prerequisite(data['prerequisite'])
        else:
            challenge.prerequisite = ''
        if 'tags' in data:
            challenge.set_tags(data['tags'])
        if challenge.unlocked and not old_unlocked:
            news = 'Challenge "%s" unlocked!' % challenge.name
            models.News.game_broadcast(message=news)

        app.logger.info('Challenge %s updated by %r.',
                        challenge, models.User.current())

        models.commit()
        cache.clear()
        return challenge

    def delete(self, challenge_id):
        challenge = models.Challenge.query.get_or_404(challenge_id)
        models.db.session.delete(challenge)
        models.commit()
        cache.clear()


class ChallengeList(flask_restful.Resource):
    """Create & manage challenges for admins."""

    decorators = [utils.login_required, utils.require_started]

    resource_fields = {
        'challenges': fields.Nested(Challenge.resource_fields)
    }

    @staticmethod
    def _tease_challenge(chall):
        """Hide parts to be teased."""
        res = {k: getattr(chall, k) for k in Challenge.resource_fields}
        for f in ('description', 'attachments'):
            del res[f]
        return res

    @flask_restful.marshal_with(resource_fields)
    def get(self):
        if utils.is_admin():
            return dict(challenges=list(models.Challenge.query.all()))
        t = models.Team.current()
        challs = []
        for c in models.Challenge.query.all():
            if c.unlocked_for_team(t):
                challs.append(c)
            elif c.teaser:
                challs.append(self._tease_challenge(c))
        return {'challenges': challs}

    @utils.admin_required
    @flask_restful.marshal_with(Challenge.resource_fields)
    def post(self):
        data = flask.request.get_json()
        unlocked = data.get('unlocked', False)
        answer = utils.normalize_input(data['answer'])
        if not validators.IsValidator(data.get('validator', None)):
            raise errors.ValidationError('Invalid validator.')
        chall = models.Challenge.create(
            data['name'],
            data['description'],
            data['points'],
            '',
            unlocked,
            data.get('validator', validators.GetDefaultValidator()))
        validator = validators.GetValidatorForChallenge(chall)
        validator.change_answer(answer)
        if 'attachments' in data:
            chall.set_attachments(data['attachments'])
        if 'prerequisite' in data:
            chall.set_prerequisite(data['prerequisite'])
        if 'tags' in data:
            chall.set_tags(data['tags'])

        if unlocked and utils.GameTime.open():
            news = 'New challenge created: "%s"' % chall.name
            models.News.game_broadcast(message=news)

        models.commit()
        app.logger.info('Challenge %s created by %r.',
                        chall, models.User.current())
        return chall


class Tag(flask_restful.Resource):
    """Single tag for challenges."""

    decorators = [utils.login_required, utils.require_started]

    tag_fields = {
        'name': fields.String,
        'tagslug': fields.String,
        'description': fields.String
    }
    resource_fields = tag_fields.copy()
    resource_fields['challenges'] = fields.Nested(Challenge.resource_fields)

    @flask_restful.marshal_with(resource_fields)
    def get(self, tag_slug):
        tag = models.Tag.query.get_or_404(tag_slug)
        return self.get_challenges(tag)

    @utils.admin_required
    @flask_restful.marshal_with(resource_fields)
    def put(self, tag_slug):
        tag = models.Tag.query.get_or_404(tag_slug)
        tag.name = get_field('name')
        tag.description = get_field('description', tag.description)

        app.logger.info('Tag %s updated by %r', tag, models.User.current())
        models.commit()
        cache.clear()
        return self.get_challenges(tag)

    @utils.admin_required
    def delete(self, tag_slug):
        tag = models.Tag.query.get_or_404(tag_slug)
        models.db.session.delete(tag)
        cache.clear()
        models.commit()

    @classmethod
    def get_challenges(cls, tag):
        if models.User.current() and models.User.current().admin:
            challenges = tag.challenges
        else:
            raw = tag.get_challenges()
            challenges = []
            for ch in raw:
                if ch.unlocked_for_team(models.Team.current()):
                    challenges.append(ch)
                elif ch.teaser:
                    challenges.append(ChallengeList._tease_challenge(ch))
        res = {k: getattr(tag, k) for k in cls.tag_fields}
        res['challenges'] = list(challenges)
        return res


class TagList(flask_restful.Resource):
    """List of all tags"""

    decorators = [utils.login_required, utils.require_started]

    resource_fields = {
        'tags': fields.Nested(Tag.tag_fields)
    }

    @cache.rest_team_cache('tags/%d')
    @flask_restful.marshal_with(resource_fields)
    def get(self):
        q = models.Tag.query.all()
        return dict(tags=q)

    @utils.admin_required
    @flask_restful.marshal_with(Tag.tag_fields)
    def post(self):
        tag = models.Tag.create(
            get_field('name'),
            get_field('description', ''))
        models.commit()
        app.logger.info('Tag %s created by %r.', tag, models.User.current())
        cache.clear()
        return tag


class Answer(flask_restful.Resource):
    """Submit an answer."""

    decorators = [utils.login_required,
                  utils.require_submittable]

    # TODO: get answers for admin?

    def post(self):
        data = flask.request.get_json()
        if utils.is_admin():
            return self.post_admin(data)
        return self.post_player(data)

    @utils.admin_required
    def post_admin(self, data):
        cid = data.get('cid', None)
        tid = data.get('tid', None)
        if not cid or not tid:
            raise errors.ValidationError('Requires team and challenge.')
        challenge = models.Challenge.query.get(data['cid'])
        team = models.Team.query.get(data['tid'])
        if not challenge or not team:
            raise errors.ValidationError('Requires team and challenge.')
        user = models.User.current()
        app.challenge_log.info(
                'Admin %s <%s> submitting flag for challenge %s <%d>, '
                'team %s <%d>',
                user.nick, user.email, challenge.name, challenge.cid,
                team.name, team.tid)
        try:
            points = controllers.save_team_answer(challenge, team, None)
            models.commit()
        except (errors.IntegrityError, errors.FlushError) as ex:
            app.logger.exception(
                    'Unable to save answer for %s/%s: %s',
                    str(data['tid']), str(data['tid']), str(ex))
            models.db.session.rollback()
            raise errors.AccessDeniedError(
                'Unable to save answer for team. See log for details.')
        cache.delete('cats/%d' % tid)
        cache.delete('scoreboard')
        return dict(points=points)

    def post_player(self, data):
        answer = utils.normalize_input(data['answer'])
        try:
            points = controllers.submit_answer(
                data['cid'], answer, data.get('token'))
        except errors.IntegrityError:
            raise errors.AccessDeniedError(
                    'Previously solved or flag already used.')
        try:
            models.commit()
        except (errors.IntegrityError, errors.FlushError):
            models.db.session.rollback()
            raise errors.AccessDeniedError("You've already solved that one!")
        cache.delete_team('cats/%d')
        cache.delete('scoreboard')
        return dict(points=points)


class Validator(flask_restful.Resource):
    """Allow admins to test an answer."""

    decorators = [utils.admin_required]

    def post(self):
        data = flask.request.get_json()
        answer = utils.normalize_input(data['answer'])
        try:
            correct = controllers.test_answer(data['cid'], answer)
        except errors.IntegrityError:
            raise errors.InvalidAnswerError('Invalid answer.')
        if not correct:
            raise errors.InvalidAnswerError('Invalid answer.')
        return dict(message='Answer OK.')


api.add_resource(Tag, '/api/tags/<string:tag_slug>')
api.add_resource(TagList, '/api/tags')
api.add_resource(ChallengeList, '/api/challenges')
api.add_resource(Challenge, '/api/challenges/<int:challenge_id>')
api.add_resource(Answer, '/api/answers')
api.add_resource(Validator, '/api/validator')


class APIScoreboard(flask_restful.Resource):
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
    @flask_restful.marshal_with(resource_fields)
    def get(self):
        opts = {
            'with_history': True,
            'above_zero': not app.config.get('SCOREBOARD_ZEROS'),
        }
        return dict(scoreboard=[
            {'position': i, 'name': v.name, 'tid': v.tid,
             'score': v.score, 'history': v.score_history}
            for i, v in models.Team.enumerate(**opts)])


api.add_resource(APIScoreboard, '/api/scoreboard')


class Config(flask_restful.Resource):
    """Get basic app.config for the scoreboard.

    This should not change often as it is highly-cached on the client.
    """

    def get(self):
        datefmt = ISO8601DateTime()
        config = dict(
            teams=app.config.get('TEAMS'),
            sbname=app.config.get('TITLE'),
            news_mechanism='poll',
            news_poll_interval=app.config.get('NEWS_POLL_INTERVAL'),
            csrf_token=csrfutil.get_csrf_token(),
            rules=app.config.get('RULES'),
            game_start=datefmt.format(utils.GameTime.start),
            game_end=datefmt.format(utils.GameTime.end),
            login_url=auth.get_login_uri(),
            register_url=auth.get_register_uri(),
            login_method=app.config.get('LOGIN_METHOD'),
            scoring=app.config.get('SCORING'),
            validators=validators.ValidatorMeta(),
            proof_of_work_bits=int(app.config.get('PROOF_OF_WORK_BITS')),
            invite_only=app.config.get('INVITE_KEY') is not None,
            )
        return config


api.add_resource(Config, '/api/config')


class News(flask_restful.Resource):
    """Display and manage news."""

    resource_fields = {
        'nid': fields.Integer,
        'news_type': fields.String,
        'timestamp': ISO8601DateTime,
        'author': fields.String,
        'message': fields.String,
    }

    @flask_restful.marshal_with(resource_fields)
    def get(self):
        if models.Team.current():
            news = models.News.for_team(models.Team.current())
        else:
            news = models.News.for_public()
        return list(news)

    @utils.admin_required
    @flask_restful.marshal_with(resource_fields)
    def post(self):
        data = flask.request.get_json()
        tid = None
        if 'tid' in data:
            try:
                tid = int(data['tid'])
            except ValueError:
                pass
        author = models.User.current().nick
        if tid:
            item = models.News.unicast(tid, author, data['message'])
        else:
            item = models.News.broadcast(author, data['message'])
        models.commit()
        return item


api.add_resource(News, '/api/news')


class Page(flask_restful.Resource):
    """Create and retrieve static pages."""

    resource_fields = {
        'path': fields.String,
        'title': fields.String,
        'contents': fields.String,
    }

    @cache.rest_cache_path
    @flask_restful.marshal_with(resource_fields)
    def get(self, path):
        app.logger.info('Path: %s', path)
        return models.Page.query.get_or_404(path)

    @utils.admin_required
    @flask_restful.marshal_with(resource_fields)
    def post(self, path):
        data = flask.request.get_json()
        page = models.Page.query.get(path)
        if not page:
            page = models.Page()
            page.path = path
            models.db.session.add(page)
        page.path = data.get('path', path)
        page.title = data.get('title', page.title)
        page.contents = data.get('contents', page.contents)
        models.commit()
        return page

    @utils.admin_required
    def delete(self, path):
        page = models.Page.query.get_or_404(path)
        models.db.session.delete(page)
        models.commit()
        return {}


class PageList(flask_restful.Resource):
    """Retrieve all pages available"""

    resource_fields = {
        'pages': fields.Nested({
            'path': fields.String,
            'title': fields.String,
        })
    }

    @flask_restful.marshal_with(resource_fields)
    def get(self):
        return dict(pages=models.Page.query.all())


api.add_resource(Page, '/api/page/<path:path>')
api.add_resource(PageList, '/api/page')


class Attachment(flask_restful.Resource):
    """"Allow updating and deleting of individual files"""

    attachment_fields = {
        'aid': fields.String,
        'filename': fields.String,
    }

    challenge_fields = {
        'name': fields.String,
        'cid': fields.Integer,
    }

    resource_fields = attachment_fields.copy()
    resource_fields['challenges'] = fields.List(
            fields.Nested(challenge_fields))

    decorators = [utils.admin_required]

    @flask_restful.marshal_with(resource_fields)
    def get(self, aid):
        return models.Attachment.query.get_or_404(aid)

    @flask_restful.marshal_with(resource_fields)
    def put(self, aid):
        attachment = models.Attachment.query.get_or_404(aid)
        attachment.filename = get_field('filename')
        attachment.set_challenges(get_field('challenges'))

        app.logger.info('Attachment %s updated by %r.',
                        attachment, models.User.current())
        models.commit()
        cache.clear()
        return attachment

    def delete(self, aid):
        attachment = models.Attachment.query.get_or_404(aid)
        # Probably do not need to delete from disk
        attachment.delete()

        app.logger.info('Attachment %s deleted by %r.',
                        attachment, models.User.current())
        models.commit()
        cache.clear()


class AttachmentList(flask_restful.Resource):
    """Allow uploading of files."""

    resource_fields = {
        'attachments': fields.Nested(Attachment.resource_fields)
    }

    decorators = [utils.admin_required]

    def post(self):
        fp = flask.request.files['file']
        aid, fpath = attachments.backend.upload(fp)
        attachment = models.Attachment.query.get(aid)
        if not attachment:
            models.Attachment.create(aid, fp.filename, fp.mimetype)
            models.commit()
            cache.clear()
        return dict(aid=aid, fpath=fpath, content_type=fp.mimetype)

    @flask_restful.marshal_with(resource_fields)
    def get(self):
        return dict(attachments=list(models.Attachment.query.all()))


api.add_resource(Attachment, '/api/attachments/<string:aid>')
api.add_resource(AttachmentList, '/api/attachments')


class BackupRestore(flask_restful.Resource):
    """Control for backup and restore."""
    decorators = [utils.admin_required]

    def get(self):
        # TODO: refactor, this is messy
        rv = {
                'challenges': list(models.Challenge.query.all()),
                'tags': list(models.Challenge.query.all()),
                }
        return (
            rv,
            200,
            {'Content-Disposition': 'attachment; filename=challenges.json'})

    def post(self):
        # TODO: refactor, this is messy
        raise NotImplementedError('Restore not implemented.')

        challs = []
        models.commit()
        cache.clear()
        return {'message': '%d Challenges imported.' % (len(challs),)}


api.add_resource(BackupRestore, '/api/backup')


class CTFTimeScoreFeed(flask_restful.Resource):
    """Provide a JSON feed to CTFTime.

    At this time, it is only intended to cover the mandatory fields in the
    feed: https://ctftime.org/json-scoreboard-feed
    """

    def get(self):
        standings = [{'pos': i, 'team': v.name, 'score': v.score}
                     for i, v in models.Team.enumerate()]
        data = {'standings': standings}
        return data, 200, {'X-No-XSSI': 1}


api.add_resource(CTFTimeScoreFeed, '/api/ctftime/scoreboard')


class Configz(flask_restful.Resource):
    """Dump the config."""

    decorators = [utils.admin_required]

    def get(self):
        return repr(app.config)


api.add_resource(Configz, '/api/configz')


class ToolsRecalculate(flask_restful.Resource):
    """Recalculate the scores."""

    decorators = [utils.admin_required]

    def post(self):
        changed = 0
        for team in models.Team.query.all():
            old = team.score
            team.update_score()
            changed += 1 if team.score != old else 0
        models.commit()
        cache.clear()
        return {'message': ('Recalculated, %d changed.' % changed)}


api.add_resource(ToolsRecalculate, '/api/tools/recalculate')


class DBReset(flask_restful.Resource):
    """Reset various parts of the database."""

    decorators = [utils.admin_required]

    def post(self):
        data = flask.request.get_json()
        if data.get('ack') != 'ack':
            raise ValueError('Requires ack!')
        op = data.get('op', '')
        if op == 'scores':
            app.logger.info('Score reset requested by %r.',
                            models.User.current())
            models.ScoreHistory.query.delete()
            models.Answer.query.delete()
            models.NonceFlagUsed.query.delete()
            for team in models.Team.query.all():
                team.score = 0
        elif op == 'players':
            app.logger.info('Player reset requested by %r.',
                            models.User.current())
            models.User.query.filter(
                    models.User.admin == False).delete()  # noqa: E712
            models.Team.query.delete()
        else:
            raise ValueError('Unknown operation %s' % op)
        models.commit()
        cache.clear()
        return {'message': 'Done'}


api.add_resource(DBReset, '/api/tools/reset')
