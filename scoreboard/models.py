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

import base64
import datetime
import flask
from flask.ext import sqlalchemy
import hashlib
import hmac
import json
import logging
import pbkdf2
import re
import sqlalchemy as sqlalchemy_base
import time
import utils
from sqlalchemy import exc
from sqlalchemy import orm
from sqlalchemy.orm import exc as orm_exc

from scoreboard.app import app
from scoreboard import attachments
from scoreboard import errors

db = sqlalchemy.SQLAlchemy(app)


class Team(db.Model):
    """A Team of Players (Team of 1 if not using Teams)."""
    tid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False, index=True)
    score = db.Column(db.Integer, default=0)  # Denormalized
    players = db.relationship(
        'User', backref=db.backref('team', lazy='joined'), lazy='dynamic')
    answers = db.relationship('Answer', backref='team', lazy='select',
            cascade='delete')
    score_history = db.relationship('ScoreHistory', backref='team',
            cascade='delete')

    def __repr__(self):
        return '<Team: %s>' % self.name

    def __str__(self):
        return self.name

    @property
    def code(self):
        return hmac.new(app.config['SECRET_KEY'], self.name.encode('utf-8')).hexdigest()[:12]

    @property
    def solves(self):
        return len(self.answers)

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
    def enumerate(cls, with_history=False):
        if not with_history:
            return enumerate(cls.query.order_by(cls.score.desc()).all(), 1)
        qry = cls.query.options(
                orm.joinedload(cls.score_history)).order_by(cls.score.desc())
        return enumerate(qry.all(), 1)


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
        db.session.add(entry)


class User(db.Model):
    """A single User for login.  Player or admin."""

    uid = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nick = db.Column(db.String(80), unique=True, nullable=False, index=True)
    pwhash = db.Column(db.String(48))  # pbkdf2.crypt == 48 bytes
    admin = db.Column(db.Boolean, default=False)
    team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'))
    create_ip = db.Column(db.String(45))     # max 45 bytes for IPv6
    last_login_ip = db.Column(db.String(45))  

    def set_password(self, password):
        self.pwhash = pbkdf2.crypt(password)

    def __repr__(self):
        return '<User: %s <%s>>' % (self.nick, self.email)

    def __str__(self):
        return self.nick

    def promote(self):
        """Promote a user to admin."""
        empty_team = self.team and set(self.team.players.all()) == set([self])
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
                app.config['SECRET_KEY'], token_plain, hashlib.sha1).digest()
        token = '%d:%s' % (expires, mac)
        return base64.urlsafe_b64encode(token)

    def verify_token(self, token, token_type='pwreset'):
        """Verify a user-specific token."""
        token = str(token)
        decoded = base64.urlsafe_b64decode(token)
        expires, mac = decoded.split(':')
        if float(expires) > time.time():
            raise errors.ValidationError('Expired token.')
        expected = self.get_token(token_type=token_type, expires=int(expires))
        if not utils.compare_digest(expected, token):
            raise errors.ValidationError('Invalid token.')
        return True

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
    def login_user(cls, email, password):
        try:
            user = cls.query.filter_by(email=email).one()
        except exc.InvalidRequestError:
            return None
        if pbkdf2.crypt(password, user.pwhash) == user.pwhash:
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


class Category(db.Model):
    """A Category of Challenges."""

    cid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    unlocked = db.Column(db.Boolean, default=True)
    challenges = db.relationship(
        'Challenge', backref=db.backref('category', lazy='joined'),
        lazy='select')

    def __repr__(self):
        return '<Category: %d/%s>' % (self.cid, self.name)

    @property
    def challenge_count(self):
        """Count of unlocked challenges."""
        if 'challenges' not in sqlalchemy_base.inspect(self).unloaded:
            return len(self.challenges)
        return self.get_challenges(sort=False).count()

    @property
    def solved_count(self):
        """Count of solved challenges for current team."""
        if 'challenges' not in sqlalchemy_base.inspect(self).unloaded:
            challs = self.challenges
        else:
            challs = self.get_challenges(sort=False)
        ct = 0
        for ch in challs:
            if ch.answered:
                ct += 1
        return ct

    def slugify(self):
        base_slug = '-'.join(w.lower() for w in re.split('\W+', self.name))
        if self.slug == base_slug:
            return
        ctr = 0
        while True:
            slug = base_slug + (('-%d' % ctr) if ctr else '')
            if not Category.query.filter(Category.slug == slug).count():
                break
            ctr += 1
        self.slug = slug

    @classmethod
    def create(cls, name, description, unlocked=True):
        try:
            cat = cls()
            cat.name = name
            cat.description = description
            cat.unlocked = unlocked
            cat.slugify()
            db.session.add(cat)
            return cat
        except exc.IntegrityError:
            db.session.rollback()

    def delete(self):
        db.session.delete(self)

    def get_challenges(self, unlocked_only=True, sort=True, force_query=False):
        if force_query or 'challenges' in sqlalchemy_base.inspect(self).unloaded:
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
        challenges = Challenge.query.filter(Challenge.category == self)
        if unlocked_only:
            unlocked_identity = True
            challenges = challenges.filter(
                Challenge.unlocked == unlocked_identity)
        if not sort:
            return challenges
        return challenges.order_by(Challenge.weight)

    @classmethod
    def joined_query(cls):
        return cls.query.options(orm.joinedload(cls.challenges)
                                .joinedload(Challenge.answers))


class Challenge(db.Model):
    """A single challenge to be played."""

    cid = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    answer_hash = db.Column(db.String(48))  # Protect answers
    unlocked = db.Column(db.Boolean, default=False)
    weight = db.Column(db.Integer, nullable=False)  # Order for display
    prerequisite = db.Column(db.Text, nullable=False)  # Prerequisite Metadata
    cat_cid = db.Column(db.Integer, db.ForeignKey('category.cid'))
    answers = db.relationship('Answer', backref='challenge', lazy='select')
    hints = db.relationship('Hint', backref='challenge', lazy='joined')
    attachments = db.relationship('Attachment', backref='challenge',
                                  lazy='joined')

    def __repr__(self):
        return '<Challenge: %d/%s>' % (self.cid, self.name)

    def is_answered(self, team=None, answers=None):
        if team is None:
            team = flask.g.team
        if not team:
            return False
        if answers:
            for a in answers:
                if a.team_tid == team.tid and a.challenge_cid == self.cid:
                    return True
            return False
        return bool(Answer.query.filter(Answer.challenge == self,
                                        Answer.team == team).count())

    def verify_answer(self, answer):
        return utils.compare_digest(
                pbkdf2.crypt(answer, self.answer_hash), self.answer_hash)

    def change_answer(self, answer):
        self.answer_hash = pbkdf2.crypt(answer)

    @property
    def solves(self):
        return len(self.answers)

    @property
    def answered(self):
        if not flask.g.team:
            return False
        return self.is_answered(answers=flask.g.team.answers)

    @property
    def teaser(self):
        if not app.config.get('TEASE_HIDDEN', True):
            return False
        if not flask.g.team:
            return False
        return not self.unlocked_for_team(flask.g.team) 

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
        return chall.is_answered(team=team)

    @classmethod
    def create(cls, name, description, points, answer, cid, unlocked=False):
        challenge = cls()
        challenge.name = name
        challenge.description = description
        challenge.points = points
        challenge.answer_hash = pbkdf2.crypt(answer)
        challenge.cat_cid = cid
        challenge.unlocked = unlocked
        weight = db.session.query(db.func.max(Challenge.weight)).scalar()
        challenge.weight = (weight + 1) if weight else 1
        challenge.prerequisite = ''
        db.session.add(challenge)
        return challenge

    def delete(self):
        db.session.delete(self)

    def set_hints(self, hints):
        hid_set = set()
        old_hints = list(self.hints)

        for h in hints:
            if h.get('hid', None):
                hint = Hint.query.get(h['hid'])
                hid_set.add(h['hid'])
            else:
                hint = Hint()
                db.session.add(hint)
                hint.challenge = self
            hint.hint = h['hint']
            hint.cost = h['cost']

        # Delete removed hints
        for h in old_hints:
            if h.hid not in hid_set:
                db.session.delete(h)

    def set_attachments(self, attachments):
        aid_set = set()
        old_attachments = list(self.attachments)

        for a in attachments:
            aid_set.add(a['aid'])
            attachment = Attachment.query.get(a['aid'])
            if not attachment:
                attachment = Attachment()
                attachment.aid = a['aid']
                attachment.filename = a['filename']
                attachment.content_type = a['content_type']
                attachment.challenge = self
                db.session.add(attachment)

        for a in old_attachments:
            if a.aid not in aid_set:
                a.delete()

    def set_prerequisite(self, prerequisite):
        if not prerequisite:
            self.prerequisite = ''
            return
        if 'type' in prerequisite and prerequisite['type'] == 'None':
            self.prerequisite = ''
        else:
            self.prerequisite = json.dumps(prerequisite)


class Attachment(db.Model):
    """Attachment to a challenge."""

    aid = db.Column(db.String(64), primary_key=True)
    challenge_cid = db.Column(db.Integer, db.ForeignKey('challenge.cid'),
            nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    content_type = db.Column(db.String(100))
    storage_path = db.Column(db.String(256))

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '<Attachment %s>' % self.aid

    def delete(self, from_disk=True):
        if from_disk:
            try:
                attachments.delete(self)
            except IOError as ex:
                app.logger.exception("Couldn't delete: %s", str(ex))
        db.session.delete(self)


class Hint(db.Model):
    """Hint for a challenge."""

    hid = db.Column(db.Integer, primary_key=True)
    challenge_cid = db.Column(db.Integer, db.ForeignKey('challenge.cid'),
            nullable=False)
    hint = db.Column(db.Text, nullable=False)
    cost = db.Column(db.Integer)

    def __repr__(self):
        return '<Hint: %d -> %d>' % (hint.hid, hint.challenge_cid)

    def unlock(self, team):
        unlocked = UnlockedHint()
        unlocked.hint = self
        unlocked.team = team
        unlocked.timestamp = datetime.datetime.utcnow()
        if flask.request:
            unlocked.src_ip = flask.request.remote_addr
        db.session.add(unlocked)
        return unlocked

    def is_unlocked(self, team=None, unlocked_hints=None):
        if team is None:
            team = flask.g.team
        if not team:
            return flask.g.user and flask.g.user.admin
        if unlocked_hints:
            for h in unlocked_hints:
                if h.hint_hid == self.hid and h.team_tid == team.tid:
                    return True
            return False
        try:
            UnlockedHint.query.filter(UnlockedHint.hint_hid == self.hid,
                                      UnlockedHint.team_tid == team.tid).one()
            return True
        except orm_exc.NoResultFound:
            return False


class UnlockedHint(db.Model):
    """Record that a team has unlocked a hint."""

    hint_hid = db.Column(
        db.Integer, db.ForeignKey('hint.hid'), primary_key=True)
    hint = db.relationship('Hint', backref='unlocked_by', lazy='joined')
    team_tid = db.Column(
        db.Integer, db.ForeignKey('team.tid'), primary_key=True)
    team = db.relationship('Team', backref='hints')
    timestamp = db.Column(db.DateTime)
    src_ip = db.Column(db.String(45))   # IP Where unlocked


class Answer(db.Model):
    """Log a successfully submitted answer."""

    challenge_cid = db.Column(db.Integer, db.ForeignKey('challenge.cid'),
                              primary_key=True)
    team_tid = db.Column(
        db.Integer, db.ForeignKey('team.tid'), primary_key=True)
    timestamp = db.Column(db.DateTime)
    answer_hash = db.Column(db.String(48))  # Store hash of team+answer
    submit_ip = db.Column(db.String(45))    # Source IP for submission

    @classmethod
    def create(cls, challenge, team, answer_text):
        answer = cls()
        answer.challenge = challenge
        answer.team = team
        answer.timestamp = datetime.datetime.utcnow()
        answer.answer_hash = pbkdf2.crypt(team.name + answer_text)
        if flask.request:
            answer.submit_ip = flask.request.remote_addr
        db.session.add(answer)
        return answer


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
        author = author or app.config.get('SYSTEM_NAME', 'root')
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
        return cls.query.filter(cls.news_type != 'Unicast'
                ).order_by(cls.timestamp.desc()).limit(limit)


class Page(db.Model):
    """Represent static pages to be rendered with Markdown."""

    path = db.Column(db.String(100), primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    contents = db.Column(db.Text, nullable=False)


# Shortcut for commiting
commit = db.session.commit
