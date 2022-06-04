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

import struct
import time

from markupsafe import Markup
from werkzeug import exceptions

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
        self.assertFalse(csrfutil.verify_csrf_token(token, self.test_user))
        mock_time.assert_not_called()

    def testDecorator_GET(self):
        called = mock.Mock()
        called.__name__ = 'called'
        wrapped = csrfutil.csrf_protect(called)
        with self.app.test_request_context('/'):
            wrapped()
        called.assert_called_once()

    @mock.patch.object(csrfutil, 'verify_csrf_token')
    def testDecorator_Passes(self, mock_verify):
        mock_verify.return_value = True
        called = mock.Mock()
        called.__name__ = 'called'
        wrapped = csrfutil.csrf_protect(called)
        with self.app.test_request_context('/?csrftoken=x', method='POST'):
            wrapped()
        called.assert_called_once()

    @mock.patch.object(csrfutil, 'verify_csrf_token')
    def testDecorator_Fails(self, mock_verify):
        mock_verify.return_value = False
        called = mock.Mock()
        called.__name__ = 'called'
        wrapped = csrfutil.csrf_protect(called)
        with self.app.test_request_context('/', method='POST'):
            with self.assertRaises(exceptions.Forbidden):
                wrapped()
        called.assert_not_called()

    @mock.patch.object(csrfutil, 'get_csrf_token')
    def testGetCSRFField(self, mock_get_csrf_token):
        mock_value = 'abcdef'
        mock_get_csrf_token.return_value = mock_value
        rv = csrfutil.get_csrf_field(user='foo')
        mock_get_csrf_token.assert_called_once_with(user='foo')
        self.assertTrue(isinstance(rv, Markup))
        self.assertTrue(mock_value in str(rv))

    @mock.patch.object(csrfutil, 'verify_csrf_token')
    def testCSRFProtectionMiddleware_HeaderValid(self, mock_verify_csrf_token):
        headers = [('X-XSRF-TOKEN', 'foo')]
        mock_verify_csrf_token.return_value = True
        with self.app.test_request_context(
                '/', method='POST', headers=headers):
            with mock.patch.object(self.app.config, 'get') as mock_get:
                mock_get.return_value = False
                csrfutil.csrf_protection_request()
        mock_get.assert_called_once()
        mock_verify_csrf_token.assert_called_once_with('foo')

    @mock.patch.object(csrfutil, 'verify_csrf_token')
    def testCSRFProtectionMiddleware_HeaderInvalid(
            self, mock_verify_csrf_token):
        headers = [('X-XSRF-TOKEN', 'foo')]
        mock_verify_csrf_token.return_value = False
        with self.app.test_request_context(
                '/', method='POST', headers=headers):
            with mock.patch.object(self.app.config, 'get') as mock_get:
                mock_get.return_value = False
                with self.assertRaises(exceptions.Forbidden):
                    csrfutil.csrf_protection_request()
        mock_get.assert_called_once()
        mock_verify_csrf_token.assert_called_once_with('foo')

    @mock.patch.object(csrfutil, 'verify_csrf_token')
    def testCSRFProtectionMiddleware_FormValid(self, mock_verify_csrf_token):
        mock_verify_csrf_token.return_value = True
        with self.app.test_request_context(
                '/?csrftoken=foo', method='POST'):
            with mock.patch.object(self.app.config, 'get') as mock_get:
                mock_get.return_value = False
                csrfutil.csrf_protection_request()
        mock_get.assert_called_once()
        mock_verify_csrf_token.assert_called_once_with('foo')

    @mock.patch.object(csrfutil, 'verify_csrf_token')
    def testCSRFProtectionMiddleware_GET(self, mock_verify_csrf_token):
        mock_verify_csrf_token.return_value = True
        with self.app.test_request_context('/'):
            with mock.patch.object(self.app.config, 'get') as mock_get:
                mock_get.return_value = False
                csrfutil.csrf_protection_request()
        mock_get.assert_not_called()
        mock_verify_csrf_token.assert_not_called()
