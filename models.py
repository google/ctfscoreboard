import datetime
import flask
from flask.ext import sqlalchemy
import pbkdf2
import re
from sqlalchemy import exc
from sqlalchemy.orm import exc as orm_exc

import app

db = sqlalchemy.SQLAlchemy(app.app)


class Team(db.Model):
  tid = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), unique=True)
  score = db.Column(db.Integer, default=0)  # Denormalized
  players = db.relationship('User', backref=db.backref('team', lazy='joined'),
      lazy='dynamic')
  answers = db.relationship('Answer', backref='team', lazy='dynamic')

  def __repr__(self):
    return '<Team: %s>' % self.name

  def __str__(self):
    return self.name

  @property
  def code(self):
    hmac.new(app.config['SECRET_KEY'], self.name).hexdigest()[:12]

  @property
  def solves(self):
    return self.answers.count()

  @classmethod
  def create(cls, name):
    team = cls()
    db.session.add(team)
    team.name = name
    db.session.commit()

  @classmethod
  def enumerate(cls):
    return enumerate(cls.query.order_by(cls.score.desc()).all(), 1)


class User(db.Model):
  uid = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String(120), unique=True)
  nick = db.Column(db.String(80), unique=True)
  pwhash = db.Column(db.String(48))  # pbkdf2.crypt == 48 bytes
  admin = db.Column(db.Boolean, default=False)
  team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'))

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
    db.session.commit()

  @classmethod
  def login_user(cls, email, password):
    try:
      user = cls.query.filter_by(email=email).one()
    except:
      return None
    if pbkdf2.crypt(password, user.pwhash) == user.pwhash:
      return user
    return None

  @classmethod
  def create(cls, email, nick, password, team=None):
    user = cls()
    db.session.add(user)
    user.email = email
    user.nick = nick
    user.set_password(password)
    user.team = team
    db.session.commit()
    return user


class Category(db.Model):
  cid = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100), unique=True)
  slug = db.Column(db.String(100), unique=True)
  description = db.Column(db.Text)
  unlocked = db.Column(db.Boolean, default=True)
  challenges = db.relationship('Challenge',
      backref=db.backref('category', lazy='joined'), lazy='dynamic')

  def __repr__(self):
    return '<Category: %d/%s>' % (self.cid, self.name)

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
      db.session.commit()
      return cat
    except exc.IntegrityError:
      flask.flash('Unable to create Category.', 'danger')
      db.session.rollback()

  def delete(self):
    db.session.delete(self)
    db.session.commit()

  def get_challenges(self, unlocked_only=True):
    challenges = Challenge.query.filter(Challenge.category == self)
    if unlocked_only:
      challenges = challenges.filter(Challenge.unlocked == True)
    return challenges


class Challenge(db.Model):
  cid = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100))
  description = db.Column(db.Text)
  points = db.Column(db.Integer)
  answer_hash = db.Column(db.String(48))  # Protect answers
  unlocked = db.Column(db.Boolean, default=False)
  cat_cid = db.Column(db.Integer, db.ForeignKey('category.cid'))
  answers = db.relationship('Answer', backref='challenge', lazy='dynamic')
  hints = db.relationship('Hint', backref='challenge', lazy='dynamic')

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
    return pbkdf2.crypt(answer, self.answer_hash) == self.answer_hash

  def change_answer(self, answer):
    self.answer_hash = pbkdf2.crypt(answer)

  @property
  def solves(self):
    return self.answers.count()

  @property
  def answered(self):
    if not flask.g.team:
      return False
    return self.is_answered(answers=flask.g.team.answers)

  @classmethod
  def create(cls, name, description, points, answer, cid, unlocked=False):
    challenge = cls()
    challenge.name = name
    challenge.description = description
    challenge.points = points
    challenge.answer_hash = pbkdf2.crypt(answer)
    challenge.cat_cid = cid
    challenge.unlocked = unlocked
    db.session.add(challenge)
    return challenge

  def delete(self):
    db.session.delete(self)
    db.session.commit()


class Hint(db.Model):
  hid = db.Column(db.Integer, primary_key=True)
  challenge_cid = db.Column(db.Integer, db.ForeignKey('challenge.cid'))
  hint = db.Column(db.Text)
  cost = db.Column(db.Integer)

  def unlock(self, team):
    unlocked = UnlockedHint()
    unlocked.hint = self
    unlocked.team = team
    unlocked.timestamp = datetime.datetime.utcnow()
    db.session.add(unlocked)
    db.session.commit()

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
  hint_hid = db.Column(db.Integer, db.ForeignKey('hint.hid'), primary_key=True)
  hint = db.relationship('Hint', backref='unlocked_by', lazy='joined')
  team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'), primary_key=True)
  team = db.relationship('Team', backref='hints')
  timestamp = db.Column(db.DateTime)


class Answer(db.Model):
  # Log correct answer
  challenge_cid = db.Column(db.Integer, db.ForeignKey('challenge.cid'),
      primary_key=True)
  team_tid = db.Column(db.Integer, db.ForeignKey('team.tid'), primary_key=True)
  timestamp = db.Column(db.DateTime)
  answer_hash = db.Column(db.String(48))  # Store hash of team+answer

  @classmethod
  def create(cls, challenge, team, answer_text):
    answer = cls()
    answer.challenge = challenge
    answer.team = team
    answer.timestamp = datetime.datetime.utcnow()
    answer.answer_hash = pbkdf2.crypt(team.name + answer_text)
    db.session.add(answer)
    db.session.commit()
    return answer


# Shortcut for commiting
commit = db.session.commit
