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
