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
import re
from sqlalchemy import exc
import urllib

from scoreboard import errors
from scoreboard import mail
from scoreboard import main
from scoreboard import models
from scoreboard import utils
from scoreboard import validators

app = main.get_app()


def register_user(email, nick, password, team_id=None,
                  team_name=None, team_code=None):
    """Registers a player.

    Arguments:
      email: User's email
      nick: User's nick
      password: Player's password
      team_id: Id# of team, or None to create new team.
      team_name: Name of new team.
      team_code: Validation code to join team.
    """
    if not re.match(r'[-0-9a-zA-Z.+_]+@[-0-9a-zA-Z.+_]+\.[a-zA-Z]+$',
                    email):
        raise errors.ValidationError('Invalid email address.')
    # TODO: Sanitize other fields
    first = models.User.query.count() == 0
    if not first and app.config.get('TEAMS'):
        if team_id == 'new':
            try:
                app.logger.info('Creating new team %s for user %s',
                                team_name, nick)
                team = models.Team.create(team_name)
            except exc.IntegrityError:
                models.db.session.rollback()
                raise errors.ValidationError('Team already exists!')
        else:
            team = models.Team.query.get(int(team_id))
            if not team or team_code.lower() != team.code.lower():
                raise errors.ValidationError(
                    'Invalid team selection or team code.')
    else:
        team = None
    try:
        if not team and not first:
            team = models.Team.create(nick)
        user = models.User.create(email, nick, password, team=team)
        models.commit()
    except exc.IntegrityError:
        models.db.session.rollback()
        if models.User.get_by_email(email):
            raise errors.ValidationError('Duplicate email address.')
        if models.User.get_by_nick(nick):
            raise errors.ValidationError('Duplicate nick.')
        if team_name and models.Team.get_by_name(team_name):
            raise errors.ValidationError('Duplicate team name.')
        raise errors.ValidationError('Unknown integrity error.')
    if not user.admin:
        models.ScoreHistory.add_entry(team)
        models.commit()
    app.logger.info('User %s <%s> registered from IP %s.',
                    nick, email, flask.request.remote_addr)
    return user


@utils.require_not_started
def change_user_team(uid, team_tid, code):
    """Provide an interface for changing a user's team"""
    team = models.Team.query.get_or_404(team_tid)
    user = models.User.query.get_or_404(uid)

    old_team = user.team

    if code.lower() != team.code.lower():
        raise errors.ValidationError('Invalid team selection or team code')

    if team.tid == user.team_tid:
        raise errors.ValidationError('Changing to same team')

    app.logger.info('User %s switched to team %s from %s' %
                    (user.nick, team.name, old_team.name))
    user.team = team
    user.team_tid = team_tid
    flask.session['team'] = team_tid

    if old_team.players.count() == 0 and len(old_team.answers) == 0:
        app.logger.info('Removing team %s due to lack of players' %
                        old_team.name)
        models.db.session.delete(old_team)

    models.commit()


@utils.require_submittable
def submit_answer(cid, answer):
    """Submits an answer.

    Returns:
      Number of points awarded for answer.
    """
    correct = 'WRONG'
    team = models.Team.current()
    if not team:
        raise errors.AccessDeniedError('No team!')
    try:
        challenge = models.Challenge.query.get(cid)
        if not challenge.unlocked_for_team(team):
            raise errors.AccessDeniedError('Challenge is locked!')
        validator = validators.GetValidatorForChallenge(challenge)
        if validator.validate_answer(answer, team):
            ans = models.Answer.create(challenge, team, answer)

            if utils.GameTime.over():
                correct = 'CORRECT (Game Over)'
            else:
                team.score += ans.current_points
                correct = 'CORRECT'

            team.last_solve = datetime.datetime.utcnow()
            models.ScoreHistory.add_entry(team)
            challenge.update_answers(exclude_team=team)

            if utils.GameTime.over():
                return 0
            else:
                return ans.current_points
        else:
            raise errors.InvalidAnswerError('Really?  Haha no....')
    except errors.IntegrityError:
        models.db.session.rollback()
        raise
    finally:
        user = models.User.current()
        app.challenge_log.info(
            'Player %s <%s>(%d)/Team %s(%d) submitted '
            '"%s" for Challenge %s<%d>: %s',
            user.nick, user.email, user.uid, team.name, team.tid, answer,
            challenge.name, challenge.cid, correct)


def offer_password_reset(user):
    token = user.get_token()
    token_url = utils.absolute_url('/pwreset/%s/%s' %
                                   (urllib.quote(user.email), token))
    message = flask.render_template(
            'pwreset.eml', token_url=token_url,
            user=user, ip=flask.request.remote_addr, config=app.config)
    subject = '%s Password Reset' % app.config.get('TITLE')
    try:
        mail.send(message, subject, user.email, to_name=user.nick)
    except mail.MailFailure:
        raise errors.ServerError('Could not send mail.')
