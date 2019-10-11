# Copyright 2019 Google LLC. All Rights Reserved.
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

from scoreboard.tests import base

from scoreboard import controllers
from scoreboard import errors


class RegisterTest(base.BaseTestCase):
    """Test register_user controller."""

    def testRegister_Normal(self):
        rv = controllers.register_user('foo@bar.com', 'foo', 'pass')
        self.assertIsNotNone(rv)

    def testRegister_BadEmail(self):
        """Test variations on bad emails."""
        for email in ('', 'frob', '//', '<foo@bar.com', 'foo@bar.com>'):
            with self.assertRaises(errors.ValidationError):
                controllers.register_user(email, 'foo', 'pass')

    def testRegister_DupeNick(self):
        self.app.config['TEAMS'] = False
        controllers.register_user('foo@bar.com', 'foo', 'pass')
        with self.assertRaises(errors.ValidationError):
            controllers.register_user('bar@bar.com', 'foo', 'pass')

    def testRegister_DupeTeam(self):
        self.app.config['TEAMS'] = True
        controllers.register_user(
                'foo@bar.com', 'foo', 'pass', team_id='new',
                team_name='faketeam')
        with self.assertRaises(errors.ValidationError):
            controllers.register_user(
                    'bar@bar.com', 'foo', 'pass', team_id='new',
                    team_name='faketeam')

    def testRegister_DupeEmail(self):
        self.app.config['TEAMS'] = False
        controllers.register_user('foo@bar.com', 'foo', 'pass')
        with self.assertRaises(errors.ValidationError):
            controllers.register_user('foo@bar.com', 'sam', 'pass')
