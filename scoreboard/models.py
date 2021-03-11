# Copyright 2018 Google LLC. All Rights Reserved.
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

import base64
import datetime
import flask
import flask_sqlalchemy
import hashlib
import hmac
import json
import logging
import math
import os
import re
import sqlalchemy as sqlalchemy_base
import time

from argon2 import PasswordHasher

from sqlalchemy import exc
from sqlalchemy import func
from sqlalchemy import orm
from sqlalchemy.ext import hybrid

from scoreboard import attachments
from scoreboard import errors
from scoreboard import main
from scoreboard import utils

app = main.get_app()
db = flask_sqlalchemy.SQLAlchemy(app)


class Team(db.Model):
    """A Team of Players (Team of 1 if not using Teams)."""
    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    score = db.Column(db.Integer, default=0)  # Denormalized
    last_solve = db.Column(db.DateTime, nullable=True)
    players = db.relationship(
        'User', backref=db.backref('team', lazy='joined'), lazy='dynamic')
    answers = db.relationship('Answer', backref='team', lazy='select',
                              cascade='delete')
    score_history = db.relationship(
            'ScoreHistory',
            backref=db.backref('team', lazy='joined'),
            lazy='select', cascade='delete')

    def __repr__(self):
        return '<Team: %s>' % self.name.encode('utf-8')

    def __str__(self):
        return self.name

    @property
    def code(self):
        secret_key = (app.config.get('TEAM_SECRET_KEY') or
                      app.config.get('SECRET_KEY'))
        return hmac.new(utils.to_bytes(secret_key),
                        self.name.encode('utf-8'),
                        hashlib.sha256).hexdigest()[:12]

    @property
    def solves(self):
        return len(self.answers)

    def update_score(self):
        old_score = self.score
        self.score = sum(a.current_points for a in self.answers)
        if self.score != old_score:
            # Add score history entry
            if not getattr(self, '_pending_sh', False):
                ScoreHistory.add_entry(self)
                self._pending_sh = True

    def can_access(self, user=None):
        """Check if player can access team."""
        user = user or User.current()
        if user.admin:
            return True
        return user.team == self

    @classmethod
    def create(cls, name):
        team = cls()
        db.session.add(team)
        team.name = name
        return team

    @classmethod
    def get_by_name(cls, name):
        try:
            return cls.query.filter_by(name=name).one()
        except exc.InvalidRequestError:
            return None

    @classmethod
    def enumerate(cls, with_history=False, above_zero=False):
        if with_history:
            base = cls.query.options(orm.joinedload(cls.score_history))
        else:
            base = cls.query
        if above_zero:
            base = base.filter(cls.score > 0)
        sorting = base.order_by(cls.score.desc(), cls.last_solve)
        return enumerate(sorting.all(), 1)

    @classmethod
    def all(cls, with_history=True):
        if with_history:
            base = cls.query.options(orm.joinedload(cls.score_history))
        else:
            base = cls.query
        base = base.options(orm.joinedload(cls.answers))
        base = base.order_by(cls.name)
        return base.all()

    @classmethod
    def current(cls):
        try:
            return flask.g.team
        except AttributeError:
            user = User.current()
            if user:
                flask.g.team = user.team
                return user.team
            else:
                flask.g.team = None


class ScoreHistory(db.Model):
    team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'), nullable=False,
                         primary_key=True)
    when = db.Column(db.DateTime, nullable=False, primary_key=True,
                     default=datetime.datetime.utcnow)
    score = db.Column(db.Integer, default=0, nullable=False)

    @classmethod
    def add_entry(cls, team):
        entry = cls()
        entry.team = team
        entry.score = team.score
        db.session.merge(entry)


class User(db.Model):
    """A single User for login.  Player or admin."""

    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nick = db.Column(db.String(80), unique=True, nullable=False, index=True)
    pwhash = db.Column(db.String(48))  # argon2.PasswordHasher().hash
    admin = db.Column(db.Boolean, default=False, index=True)
    team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'))
    create_ip = db.Column(db.String(45))     # max 45 bytes for IPv6
    last_login_ip = db.Column(db.String(45))
    api_key = db.Column(db.String(32), index=True)
    api_key_updated = db.Column(db.DateTime)

    def set_password(self, password):
        ph = PasswordHasher()
        self.pwhash = ph.hash(password)

    def __repr__(self):
        return '<User: %s <%s>>' % (self.nick.encode('utf-8'), self.email)

    def __str__(self):
        return self.nick

    def promote(self):
        """Promote a user to admin."""
        empty_team = self.team and set(self.team.players.all()) == set([self])
        if self.team and len(self.team.answers):
            raise AssertionError(
                'Cannot promote player whose team has solved answers!')
        self.admin = True
        team = self.team
        self.team = None
        if empty_team:
            db.session.delete(team)

    def get_token(self, token_type='pwreset', expires=None):
        """Generate a user-specific token."""
        expires = expires or int(time.time()) + 7200  # 2 hours
        token_plain = '%d:%d:%s:%s' % (
                self.uid, expires, token_type, self.pwhash)
        mac = hmac.new(
                utils.to_bytes(app.config.get('SECRET_KEY')),
                utils.to_bytes(token_plain),
                hashlib.sha1).digest()
        token = utils.to_bytes('%d:' % expires) + mac
        return base64.urlsafe_b64encode(token)

    def verify_token(self, token, token_type='pwreset'):
        """Verify a user-specific token."""
        token = utils.to_bytes(token)
        try:
            decoded = base64.urlsafe_b64decode(token)
            expires, mac = decoded.split(b':', 1)
        except ValueError:
            raise errors.ValidationError('Invalid token.')
        if float(expires) < time.time():
            raise errors.ValidationError('Expired token.')
        expected = self.get_token(token_type=token_type, expires=int(expires))
        if not utils.compare_digest(expected, token):
            raise errors.ValidationError('Invalid token.')
        return True

    def reset_api_key(self):
        """Reset a user's api key."""
        new_key = os.urandom(16)
        try:
            self.api_key = new_key.hex()  # Python 3
        except AttributeError:
            self.api_key = new_key.encode('hex')  # Python 2
        self.api_key_update = datetime.datetime.now()

    @classmethod
    def get_by_email(cls, email):
        try:
            return cls.query.filter_by(email=email).one()
        except exc.InvalidRequestError:
            return None

    @classmethod
    def get_by_nick(cls, nick):
        try:
            return cls.query.filter_by(nick=nick).one()
        except exc.InvalidRequestError:
            return None

    @classmethod
    def get_by_api_key(cls, token):
        if not token:
            return None
        try:
            return cls.query.filter_by(api_key=token).one()
        except exc.InvalidRequestError:
            return None

    @classmethod
    def login_user(cls, email, password):
        try:
            user = cls.query.filter_by(email=email).one()
        except exc.InvalidRequestError:
            return None
        ph = PasswordHasher()
        if ph.verify(user.pwhash, password):
            if flask.has_request_context():
                user.last_login_ip = flask.request.remote_addr
                db.session.commit()
            return user
        return None

    @classmethod
    def create(cls, email, nick, password, team=None):
        first_user = True if not cls.query.count() else False
        user = cls()
        db.session.add(user)
        user.email = email
        user.nick = nick
        user.set_password(password)
        if not first_user:
            user.team = team
        else:
            user.promote()
        if flask.has_request_context():
            user.create_ip = flask.request.remote_addr
        return user

    @classmethod
    def current(cls):
        try:
            return flask.g.user
        except AttributeError:
            uid = flask.session.get('user')
            if uid is not None:
                # For some reason, .get() does not join!
                user = cls.query.options(orm.joinedload(cls.team)).filter(
                        cls.uid == uid).first()
                flask.g.user = user
                flask.g.team = user.team
                if user:
                    # Bump expiration time on session
                    utils.session_for_user(user)
                return user

    @classmethod
    def all(cls):
        return cls.query.order_by(
                cls.admin.desc(),
                cls.nick).all()


tag_challenge_association = db.Table(
        'tag_chall_association', db.Model.metadata,
        db.Column('challenge_cid', db.BigInteger,
                  db.ForeignKey('challenge.cid')),
        db.Column('tag_tagslug', db.String(100),
                  db.ForeignKey('tag.tagslug')))


class Tag(db.Model):
    """A Tag to be Applied to Challenges"""

    tagslug = db.Column(db.String(100), unique=True, primary_key=True,
                        nullable=False, index=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    challenges = db.relationship('Challenge',
                                 backref=db.backref('tags', lazy='joined'),
                                 secondary='tag_chall_association',
                                 lazy='joined')

    def __repr__(self):
        return '<Tag: %s/%s>' % (self.tagslug, self.name)

    def slugify(self):
        self.tagslug = '-'.join(w.lower() for w in re.split(r'\W+', self.name))

    @classmethod
    def create(cls, name, description):
        tag = cls()
        tag.name = name
        tag.description = description
        tag.slugify()
        db.session.add(tag)
        return tag

    def get_challenges(self, unlocked_only=True, sort=True, force_query=False):
        if (force_query or
                'challenges' in sqlalchemy_base.inspect(self).unloaded):
            return self._get_challenges_query(
                    unlocked_only=unlocked_only, sort=sort)
        return self._get_challenges_cached(
                unlocked_only=unlocked_only, sort=sort)

    def _get_challenges_cached(self, unlocked_only=True, sort=True):
        challenges = self.challenges
        if unlocked_only:
            challenges = [c for c in challenges if c.unlocked]
        if sort:
            challenges = sorted(challenges, key=lambda c: c.weight)
        return challenges

    def _get_challenges_query(self, unlocked_only=True, sort=True):
        challenges = Challenge.query.filter(
                Challenge.tags.any(tagslug=self.tagslug))
        if unlocked_only:
            unlocked_identity = True
            challenges = challenges.filter(
                Challenge.unlocked == unlocked_identity)
        if not sort:
            return challenges
        return challenges.order_by(Challenge.weight)


class Challenge(db.Model):
    """A single challenge to be played."""

    cid = db.Column(db.BigInteger, primary_key=True, autoincrement=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    min_points = db.Column(db.Integer, nullable=True)
    validator = db.Column(db.String(24), nullable=False,
                          default='static_argon2')
    answer_hash = db.Column(db.String(48))  # Protect answers
    unlocked = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Integer, nullable=False)  # Order for display
    prerequisite = db.Column(db.Text, nullable=False)  # Prerequisite Metadata
    cur_points = db.Column(db.Integer, nullable=True)
    answers = db.relationship('Answer',
                              backref=db.backref('challenge', lazy='joined'),
                              lazy='select')

    def __repr__(self):
        return '<Challenge: %d/%s>' % (self.cid, self.name)

    def is_answered(self, team=None, answers=None):
        if team is None:
            team = Team.current()
        if not team:
            return False
        if answers is not None:
            for a in answers:
                if a.team_tid == team.tid and a.challenge_cid == self.cid:
                    return True
            return False
        return bool(Answer.query.filter(Answer.challenge == self,
                                        Answer.team == team).count())

    @hybrid.hybrid_property
    def solves(self):
        try:
            return self._solves
        except AttributeError:
            self._solves = len(self.answers)
            return self._solves

    @solves.expression
    def solves(cls):
        return func.count(cls.answers)

    @property
    def answered(self):
        if not Team.current():
            return False
        return self.is_answered(answers=Team.current().answers)

    @property
    def teaser(self):
        if not app.config.get('TEASE_HIDDEN'):
            return False
        if not Team.current():
            return False
        return not self.unlocked_for_team(Team.current())

    @property
    def current_points(self):
        mode = app.config.get('SCORING', 'plain')
        value = self.points
        if mode == 'plain':
            self.cur_points = value
        elif mode == 'progressive':
            speed = app.config.get('SCORING_SPEED', 12)
            min_points = 0 if self.min_points is None else self.min_points
            self.cur_points = self.log_score(
                    value, min_points, speed, self.solves)
        return self.cur_points

    @staticmethod
    def log_score(max_points, min_points, midpoint, solves):
        # Algorithm designed by symmetric
        # logit(u, l, m, s, x) =
        #       (u - l) * ((1.0 / (1.0 + exp((1.0/s) * (x - m)))) /
        #       (1.0 / (1.0 + exp((1.0/s) * (1 - m))))) + l
        if solves == 0:
            return max_points

        def log_func(midpoint, solves):
            spread = midpoint / 3.0
            delta = solves - midpoint
            return (
                    1.0 / (1.0 + math.exp((1.0 / spread) * delta)))
        max_delta = (max_points - min_points)
        base_point = log_func(midpoint, 1.0)
        cur_point = log_func(midpoint, solves)
        return math.ceil(max_delta * cur_point / base_point + min_points)

    def unlocked_for_team(self, team):
        """Checks if prerequisites are met for this team."""
        if not self.unlocked:
            return False
        if not self.prerequisite:
            return True
        try:
            prereq = json.loads(self.prerequisite)
        except ValueError:
            logging.error('Unable to parse prerequisite data for challenge %d',
                          self.cid)
            return False
        if prereq['type'] == 'None':
            return True
        if not team:
            return False
        try:
            eval_func = getattr(self, 'prereq_' + prereq['type'])
        except AttributeError:
            logging.error(
                'Could not find prerequisite function for challenge %d',
                self.cid)
            return False
        return eval_func(prereq, team)

    def prereq_solved(self, prereq, team):
        """Require that another challenge be solved first."""
        chall = Challenge.query.get(int(prereq['challenge']))
        if not chall:
            logging.error('Challenge %d prerequisite depends on '
                          'non-existent challenge %d.', self.cid,
                          int(prereq['challenge']))
            return False
        return chall.is_answered(team=team, answers=team.answers)

    @classmethod
    def create(cls, name, description, points, answer, unlocked=False,
               validator='static_argon2'):
        challenge = cls()
        challenge.name = name
        challenge.description = description
        challenge.cid = utils.generate_id()
        challenge.points = points
        challenge.answer_hash = answer
        challenge.unlocked = unlocked
        challenge.validator = validator
        weight = db.session.query(db.func.max(Challenge.weight)).scalar()
        challenge.weight = (weight + 1) if weight else 1
        challenge.prerequisite = ''
        db.session.add(challenge)
        return challenge

    def add_tags(self, tags):
        for tag in tags:
            self.tags.append(tag)

    def delete(self):
        db.session.delete(self)

    def set_attachments(self, attachments):
        aid_set = set()
        old_attachments = list(self.attachments)

        for a in attachments:
            aid_set.add(a['aid'])
            attachment = Attachment.query.get(a['aid'])
            if not attachment:
                logging.warning(
                        'Trying to add attachment %s that does not exist: %s' %
                        (a['filename'], a['aid']))
            self.attachments.append(attachment)

        for a in old_attachments:
            if a.aid not in aid_set:
                self.attachments.remove(a)

    def set_prerequisite(self, prerequisite):
        if not prerequisite:
            self.prerequisite = ''
            return
        if 'type' in prerequisite and prerequisite['type'] == 'None':
            self.prerequisite = ''
        else:
            self.prerequisite = json.dumps(prerequisite)

    def set_tags(self, tags):
        tag_set = set()
        old_tags = list(self.tags)

        for t in tags:
            tag_set.add(t['tagslug'])
            tag = Tag.query.get(t['tagslug'])
            if tag:
                self.tags.append(tag)
            else:
                app.logger.warning('Skipping tag %s which does not exist' %
                                   t['tagslug'])

        for t in old_tags:
            if t.tagslug not in tag_set:
                self.tags.remove(t)

    def update_answers(self, exclude_team=None):
        """Update answers for variable scoring."""
        mode = app.config.get('SCORING')
        if mode == 'plain':
            return
        if mode == 'progressive':
            for a in self.answers:
                if a.team == exclude_team:
                    continue
                a.team.update_score()

    @classmethod
    def get_joined_query(cls):
        """Get a prejoined-query with answers and teams."""
        return cls.query.options(
                orm.joinedload(cls.answers).joinedload(Answer.team))


attach_challenge_association = db.Table(
        'attach_chall_association', db.Model.metadata,
        db.Column(
            'challenge_cid', db.BigInteger,
            db.ForeignKey('challenge.cid')),
        db.Column(
            'attachment_aid', db.String(64),
            db.ForeignKey('attachment.aid')))


class Attachment(db.Model):
    """Attachment to a challenge."""

    aid = db.Column(db.String(64), primary_key=True)
    filename = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(100))
    storage_path = db.Column(db.String(256))

    challenges = db.relationship(
            'Challenge', backref=db.backref('attachments', lazy='joined'),
            secondary='attach_chall_association', lazy='joined')

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '<Attachment %s>' % self.aid

    def delete(self, from_disk=True):
        if from_disk:
            try:
                attachments.backend.delete(self)
            except IOError as ex:
                app.logger.exception("Couldn't delete: %s", str(ex))
        db.session.delete(self)

    def set_challenges(self, challenges):
        cid_set = set()
        old_challenges = list(self.challenges)

        for a in challenges:
            cid_set.add(a['cid'])
            challenge = Challenge.query.get(a['cid'])
            if not challenge:
                app.logger.warning('No challenge found with cid %d' % a['cid'])
                continue
            self.challenges.append(challenge)

        for a in old_challenges:
            if a.cid not in cid_set:
                self.challenges.remove(a)

    @classmethod
    def create(cls, aid, filename, content_type):
        attachment = cls()
        attachment.aid = aid
        attachment.filename = filename
        attachment.content_type = content_type
        db.session.add(attachment)
        return attachment


class Answer(db.Model):
    """Log a successfully submitted answer."""

    challenge_cid = db.Column(
        db.BigInteger, db.ForeignKey('challenge.cid'), primary_key=True)
    team_tid = db.Column(
        db.Integer, db.ForeignKey('team.tid'), primary_key=True)
    timestamp = db.Column(db.DateTime)
    answer_hash = db.Column(db.String(48))  # Store hash of team+answer
    submit_ip = db.Column(db.String(45))    # Source IP for submission
    first_blood = db.Column(db.Integer, default=0, nullable=False)

    @classmethod
    def create(cls, challenge, team, answer_text):
        ph = PasswordHasher()
        answer = cls()
        answer.first_blood = 0
        if not challenge.solves:
            if app.config.get('FIRST_BLOOD_MIN', 0) <= challenge.points:
                answer.first_blood = app.config.get('FIRST_BLOOD', 0)
        answer.challenge = challenge
        answer.team = team
        answer.timestamp = datetime.datetime.utcnow()
        if answer_text:
            answer.answer_hash = ph.hash(team.name + answer_text)
        if flask.request:
            answer.submit_ip = flask.request.remote_addr
        db.session.add(answer)
        # remove cache here
        del challenge._solves
        return answer

    @property
    def current_points(self):
        if utils.GameTime.state(self.timestamp) == "AFTER":
            return 0

        return self.challenge.current_points + self.first_blood


class News(db.Model):
    """News updates & broadcasts."""

    NEWS_TYPES = [
            'Broadcast',  # Admin broadcast
            'Unicast',  # Team-specific update
    ]

    nid = db.Column(db.Integer, primary_key=True)
    news_type = db.Column(db.Enum(*NEWS_TYPES), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    author = db.Column(db.String(100))
    message = db.Column(db.Text)
    audience_team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'))
    audience_team = db.relationship('Team')

    @classmethod
    def broadcast(cls, author, message):
        news = cls(
                news_type='Broadcast',
                author=author,
                message=message)
        db.session.add(news)
        return news

    @classmethod
    def game_broadcast(cls, author=None, message=None):
        if message is None:
            raise ValueError('Missing message.')
        author = author or app.config.get('SYSTEM_NAME')
        if not utils.GameTime.open():
            return
        return cls.broadcast(author, message)

    @classmethod
    def unicast(cls, team, author, message):
        news = cls(
                news_type='Unicast',
                author=author,
                message=message)
        if isinstance(team, Team):
            news.audience_team = team
        elif isinstance(team, int):
            news.audience_team_tid = team
        else:
            raise ValueError('Invalid value for team.')
        db.session.add(news)
        return news

    @classmethod
    def for_team(cls, team, limit=10):
        return cls.query.filter(
                ((cls.news_type != 'Unicast') |
                    (cls.audience_team == team))
                ).order_by(cls.timestamp.desc()).limit(limit)

    @classmethod
    def for_public(cls, limit=10):
        return cls.query.filter(
                cls.news_type != 'Unicast'
                ).order_by(cls.timestamp.desc()).limit(limit)


class Page(db.Model):
    """Represent static pages to be rendered with Markdown."""

    path = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    contents = db.Column(db.Text, nullable=False)


class NonceFlagUsed(db.Model):
    """Single-time used flags."""

    challenge_cid = db.Column(db.BigInteger, db.ForeignKey('challenge.cid'),
                              primary_key=True)
    nonce = db.Column(db.BigInteger, primary_key=True)
    team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'))

    @classmethod
    def create(cls, challenge, nonce, team):
        entity = cls()
        entity.challenge_cid = challenge.cid
        entity.nonce = nonce
        entity.team_tid = team.tid
        db.session.add(entity)


# Shortcut for commiting
def commit():
    db.session.commit()
