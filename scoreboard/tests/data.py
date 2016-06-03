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
import json
import random

from scoreboard import models


def make_admin():
    u = models.User.create('admin@example.com', 'admin', 'admin')
    u.promote()
    return u


def make_teams():
    teams = []
    for name in ('QQQ', 'Light Cats', 'Siberian Nopsled'):
        teams.append(models.Team.create(name))
    return teams


def make_players(teams):
    players = []
    for name in ('Ritam', 'Dr34dc0d3', 'alpha', 'beta', 'gamma', 'delta',
                 'Dade', 'Kate'):
        team = random.choice(teams)
        players.append(models.User.create(
            name.lower() + '@example.com', name, 'password', team=team))
    return players


def make_categories():
    categories = []
    for name in ('Pwning', 'Reversing', 'Web', 'Crypto'):
        categories.append(models.Category.create(name, name + ' Category'))
    return categories


def make_challenges(cats):
    challs = []
    chall_words = (
            'Magic', 'Grand', 'Fast', 'Hash', 'Table', 'Password',
            'Crypto', 'Alpha', 'Beta', 'Win', 'Socket', 'Ball',
            'Stego', 'Word', 'Gamma', 'Native', 'Mine', 'Dump',
            'Tangled', 'Hackers', 'Book', 'Delta', 'Shadow',
            'Lose', 'Draw', 'Long', 'Pointer', 'Free', 'Not',
            'Only', 'Live', 'Secret', 'Agent', 'Hax0r', 'Whiskey',
            'Tango', 'Foxtrot')
    for _ in xrange(25):
        title = random.sample(chall_words, 3)
        random.shuffle(title)
        title = ' '.join(title)
        flag = '_'.join(random.sample(chall_words, 4)).lower()
        cat = random.choice(cats)
        points = random.randint(1, 20) * 100
        desc = 'Flag: ' + flag
        ch = models.Challenge.create(title, desc, points, flag, cat.slug,
                unlocked=True)
        hints = []
        for _ in xrange(random.randint(0, 3)):
            hints.append({'hint': 'Some hint', 'cost': points/4})
        ch.set_hints(hints)
        if len(challs) % 8 == 7:
            ch.prerequisite = json.dumps(
                    {'type': 'solved', 'challenge': challs[-1].cid})
        # TODO: attachments
        challs.append(ch)
        models.commit()
    return challs


def make_answers(teams, challs):
    for team in teams:
        times = sorted([random.randint(0, 24*60) for _ in xrange(8)],
                reverse=True)
        for ch in random.sample(challs, random.randint(1, 8)):
            a = models.Answer.create(ch, team, '')
            ago = datetime.timedelta(minutes=times.pop(0))
            a.timestamp = datetime.datetime.utcnow() - ago
            team.score += ch.points
            h = models.ScoreHistory()
            h.team = team
            h.score = team.score
            h.when = a.timestamp
            models.db.session.add(h)


def create_all():
    make_admin()

    # Teams and players
    teams = make_teams()
    players = make_players(teams)

    # Categories and challenges
    cats = make_categories()
    models.commit()  # Need IDs allocated
    challs = make_challenges(cats)

    # Submitted answers
    make_answers(teams, challs)
    models.commit()
