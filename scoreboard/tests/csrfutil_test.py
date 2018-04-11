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

import struct
import time

from scoreboard.tests import base

from scoreboard import csrfutil

try:
    import mock
except ImportError:
    from unittest import mock


class CSRFUtilTest(base.BaseTestCase):
    """Test CSRF protection."""

    base_clock = 1523481076.571611
    valid_token = 'dMvPWgUhaJbF18mqeuMyWspjUplsvb1x4Z139GbPFAjlzhLO'
    test_user = 'user'

    @mock.patch.object(time, 'time')
    def testGetCSRFToken(self, mock_time):
        mock_time.return_value = self.base_clock
        self.assertEqual(self.valid_token,
                         csrfutil.get_csrf_token(self.test_user))
        mock_time.assert_called_once_with()

    @mock.patch.object(time, 'time')
    def testVerifyCSRFToken_Valid(self, mock_time):
        mock_time.return_value = self.base_clock
        self.assertTrue(csrfutil.verify_csrf_token(
            self.valid_token, self.test_user))
        mock_time.assert_called_once_with()

    @mock.patch.object(time, 'time')
    def testVerifyCSRFToken_Expired(self, mock_time):
        mock_time.return_value = self.base_clock + (60 * 60 * 60)
        self.assertFalse(csrfutil.verify_csrf_token(
            self.valid_token, self.test_user))
        mock_time.assert_called_once_with()

    @mock.patch.object(time, 'time')
    def testVerifyCSRFToken_InvalidSig(self, mock_time):
        mock_time.return_value = self.base_clock
        token = self.valid_token.replace('svb', 'xxx')
        self.assertFalse(csrfutil.verify_csrf_token(token, self.test_user))
        mock_time.assert_called_once_with()

    @mock.patch.object(time, 'time')
    def testVerifyCSRFToken_TamperedTime(self, mock_time):
        mock_time.return_value = self.base_clock
        token = self.valid_token.replace('dMv', 'xxx')
        self.assertFalse(csrfutil.verify_csrf_token(token, self.test_user))
        mock_time.assert_called_once_with()

    @mock.patch.object(time, 'time')
    def testVerifyCSRFToken_Truncated(self, mock_time):
        mock_time.return_value = self.base_clock
        token = self.valid_token[:4]
        with self.assertRaises(struct.error):
            csrfutil.verify_csrf_token(token, self.test_user)
        mock_time.reset_mock()
        token = 'a'
        with self.assertRaises(TypeError):
            csrfutil.verify_csrf_token(token, self.test_user)
        mock_time.assert_not_called()
