# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests for models."""

import mock
import time

from scoreboard.tests import base

from scoreboard import models


class TeamTest(base.BaseTestCase):

    def setUp(self):
        super(TeamTest, self).setUp()
        self.team = models.Team.create('Test Team')

    def testCreateTeam(self):
        foo = 'Some team name'
        rv = models.Team.create(foo)
        self.assertTrue(isinstance(rv, models.Team))
        self.assertEqual(foo, rv.name)
        self.assertEqual(foo, str(rv))
        self.assertTrue(foo in repr(rv))

    def testUpdateScore(self):
        foo = 'team'
        t = models.Team.create(foo)
        t.update_score()
        self.assertEqual(0, t.score)
        t.answers = [mock.MagicMock(), mock.MagicMock()]
        t.answers[0].current_points = 100
        t.answers[1].current_points = 200
        t.update_score()
        self.assertEqual(300, t.score)

    def testGetByName(self):
        foo = 'team'
        models.Team.create(foo)
        rv = models.Team.get_by_name(foo)
        self.assertEqual(foo, rv.name)
        self.assertIsNone(models.Team.get_by_name('does-not-exist'))


class UserTest(base.BaseTestCase):

    def setUp(self):
        super(UserTest, self).setUp()
        self.team = models.Team.create('Test Team')
        self.user = models.User.create('test@test.com', 'test', '', self.team)
        models.commit()

    def testGetByNick(self):
        nick = 'test'
        self.assertEqual(nick, models.User.get_by_nick(nick).nick)
        self.assertIsNone(models.User.get_by_nick(nick*2))

    @mock.patch.object(time, 'time')
    def testGetToken(self, mock_time):
        mock_time.return_value = 12345.678
        self.user.pwhash = '$1$foo'
        with mock.patch.object(self.app.config, 'get') as mock_get:
            mock_get.return_value = 'foo'
            token = self.user.get_token()
        mock_get.assert_called_once_with('SECRET_KEY')
        mock_time.assert_called_once_with()
        self.assertEqual('MTk1NDU6P0O68xiZ-H9gOLWPLzFkW8fhAQ8=', token)
