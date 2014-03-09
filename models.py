import datetime
import flask
from flask.ext import sqlalchemy
import pbkdf2
from sqlalchemy import exc

import app

db = sqlalchemy.SQLAlchemy(app.app)


class Team(db.Model):
  tid = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(120), unique=True)
  score = db.Column(db.Integer, default=0)  # Denormalized
  players = db.relationship('User', backref='team', lazy='dynamic')
  answers = db.relationship('Answer', backref='team', lazy='dynamic')

  def __repr__(self):
    return '<Team: %s>' % self.name

  def __str__(self):
    return self.name

  @property
  def code(self):
    hmac.new(app.config['SECRET_KEY'], self.name).hexdigest()[:12]

  @classmethod
  def create(cls, name):
    team = cls()
    db.session.add(team)
    team.name = name
    db.session.commit()


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
    return '<User: %s <%s>>' % (nick, email)

  def __str__(self):
    return self.nick

  @classmethod
  def login_user(cls, email, password):
    user = cls.query.filter_by(email=email).first()
    if pbkdf2.crypt(password, user.pwhash) == user.pwhash:
      return user
    return None

  @classmethod
  def create(cls, email, nick, password, team=None):
    if team is None:
      # Player = team mode
      team = Team()
      team.name = nick
      db.session.add(team)
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
  description = db.Column(db.Text)
  unlocked = db.Column(db.Boolean, default=True)
  challenges = db.relationship('Challenge', backref='category', lazy='dynamic')

  @classmethod
  def create(cls, name, description, unlocked=True):
    try:
      cat = cls()
      cat.name = name
      cat.description = description
      cat.unlocked = unlocked
      db.session.add(cat)
      db.session.commit()
      return cat
    except exc.IntegrityError:
      flask.flash('Unable to create Category.', 'danger')
      db.session.rollback()

  def delete(self):
    db.session.delete(self)
    db.session.commit()


class Challenge(db.Model):
  cid = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(100))
  description = db.Column(db.Text)
  points = db.Column(db.Integer)
  answer_hash = db.Column(db.String(48))  # Protect answers
  unlocked = db.Column(db.Boolean, default=False)
  cat_cid = db.Column(db.Integer, db.ForeignKey('category.cid'))
  answers = db.relationship('Answer', backref='challenge', lazy='dynamic')

  def is_answered(self, team=None):
    if team is None:
      team = flask.g.team
    return bool(Answer.query.filter(Answer.challenge == self,
        Answer.team == team).count())

  def verify_answer(self, answer):
    return pbkdf2.crypt(answer, self.answer_hash) == self.answer_hash

  def change_answer(self, answer):
    self.answer_hash = pbkdf2.crypt(answer)

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
    db.session.commit()
    return challenge

  def delete(self):
    db.session.delete(self)
    db.session.commit()


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
