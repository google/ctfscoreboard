# Copyright 2016 Google LLC. All Rights Reserved.
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

"""Base test module, MUST be imported first."""

import contextlib
import copy
import functools
import json
import logging
import os
import os.path
import pbkdf2
import time
import unittest

import flask
from flask import testing
import flask_testing
from sqlalchemy import event

from scoreboard import attachments
from scoreboard import cache
from scoreboard import main
from scoreboard import models
from scoreboard import utils


class BaseTestCase(flask_testing.TestCase):
    """Base TestCase for scoreboard.

    Monkey-patches the app and db objects.
    """

    TEST_CONFIG = dict(
        PRESERVE_CONTEXT_ON_EXCEPTION=False,
        SECRET_KEY='testing-session-key',
        SQLALCHEMY_DATABASE_URI="sqlite://",
        TEAMS=True,
        TEAM_SECRET_KEY='different-secret',
        TESTING=True,
        DEBUG=False,
        ATTACHMENT_BACKEND='test://volatile',
    )

    def create_app(self):
        """Called by flask_testing."""
        app = main.get_app()
        app.config.update(self.TEST_CONFIG)
        attachments.patch("test")
        main.setup_logging(app)
        return app

    def setUp(self):
        """Re-setup the DB to ensure a fresh instance."""
        super(BaseTestCase, self).setUp()
        # Reset config on each call
        try:
            app = main.get_app()
            app.config = copy.deepcopy(self.app._SAVED_CONFIG)
        except AttributeError:
            self.app._SAVED_CONFIG = copy.deepcopy(app.config)
        models.db.init_app(app)
        models.db.create_all()
        cache.global_cache = cache.NullCache()  # Reset cache

    def tearDown(self):
        models.db.session.remove()
        models.db.drop_all()
        super(BaseTestCase, self).tearDown()

    def queryLimit(self, limit=None):
        return MaxQueryBlock(self, limit)

    def assertItemsEqual(self, a, b, msg=None):
        a = list(a)
        b = list(b)
        a.sort()
        b.sort()
        if len(a) == len(b):
            success = True
            for c, d in zip(a, b):
                if c != d:
                    success = False
                    break
            if success:
                return None
        if msg is not None:
            raise AssertionError(msg)
        raise AssertionError('Items not equal: %r != %r', a, b)


class RestTestCase(BaseTestCase):
    """Special features for testing rest handlers."""

    def setUp(self):
        super(RestTestCase, self).setUp()
        # Monkey patch pbkdf2 for speed
        self._orig_pbkdf2 = pbkdf2.crypt
        pbkdf2.crypt = self._pbkdf2_dummy
        # Setup some special clients
        self.admin_client = AdminClient(
                self.app, self.app.response_class)
        self.authenticated_client = AuthenticatedClient(
                self.app, self.app.response_class)

    def tearDown(self):
        super(RestTestCase, self).tearDown()
        pbkdf2.crypt = self._orig_pbkdf2

    def postJSON(self, path, data, client=None):
        client = client or self.client
        return client.post(
                path, data=json.dumps(data),
                content_type='application/json')

    def putJSON(self, path, data, client=None):
        client = client or self.client
        return client.put(
                path, data=json.dumps(data),
                content_type='application/json')

    @contextlib.contextmanager
    def swapClient(self, client):
        old_client = self.client
        self.client = client
        yield
        self.client = old_client

    @staticmethod
    def _pbkdf2_dummy(value, *unused_args):
        return value


class AuthenticatedClient(testing.FlaskClient):
    """Like TestClient, but authenticated."""

    def __init__(self, *args, **kwargs):
        super(AuthenticatedClient, self).__init__(*args, **kwargs)
        self.team = models.Team.create('team')
        self.password = 'hunter2'
        self.user = models.User.create(
                'auth@example.com', 'Authenticated',
                self.password, team=self.team)
        models.db.session.commit()
        self.uid = self.user.uid
        self.tid = self.team.tid

    def open(self, *args, **kwargs):
        with self.session_transaction() as sess:
            sess['user'] = self.uid
            sess['team'] = self.tid
            sess['expires'] = time.time() + 3600
        return super(AuthenticatedClient, self).open(*args, **kwargs)


class AdminClient(testing.FlaskClient):
    """Like TestClient, but admin."""

    def __init__(self, *args, **kwargs):
        super(AdminClient, self).__init__(*args, **kwargs)
        self.user = models.User.create('admin@example.net', 'Admin', 'hunter2')
        self.user.admin = True
        models.db.session.commit()
        self.uid = self.user.uid

    def open(self, *args, **kwargs):
        with self.session_transaction() as sess:
            sess['user'] = self.uid
            sess['admin'] = True
            sess['expires'] = time.time() + 3600
        return super(AdminClient, self).open(*args, **kwargs)


class MaxQueryBlock(object):
    """Run a certain block with a maximum number of queries."""

    def __init__(self, test=None, max_count=None):
        self.max_count = max_count
        self.queries = []
        self._sql_listen_args = (
                models.db.engine, 'before_cursor_execute',
                self._count_query)
        self.test_id = test.id() if test else ''

    def __enter__(self):
        event.listen(*self._sql_listen_args)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        event.remove(*self._sql_listen_args)
        if exc_type is not None:
            return False
        if self.test_id:
            limit_msg = ((' Limit: %d.' % self.max_count)
                         if self.max_count is not None else '')
            logging.info('%s executed %d queries.%s',
                         self.test_id, len(self.queries), limit_msg)
        if self.max_count is None:
            return
        if len(self.queries) > self.max_count:
            message = ('Maximum query count exceeded: limit %d, executed %d.\n'
                       '----QUERIES----\n%s\n----END----') % (
                            self.max_count,
                            len(self.queries),
                            '\n'.join(self.queries))
            raise AssertionError(message)

    @property
    def query_count(self):
        return len(self.queries)

    def _count_query(self, unused_conn, unused_cursor, statement, parameters,
                     unused_context, unused_executemany):
        statement = '%s (%s)' % (
                statement, ', '.join(str(x) for x in parameters))
        self.queries.append(statement)
        logging.debug('SQLAlchemy: %s', statement)


def authenticated_test(f):
    """Swaps out the client for an authenticated client."""
    @functools.wraps(f)
    def wrapped_test(self):
        with self.swapClient(self.authenticated_client):
            return f(self)
    return wrapped_test


def admin_test(f):
    """Swaps out the client for an admin client."""
    @functools.wraps(f)
    def wrapped_test(self):
        with self.swapClient(self.admin_client):
            return f(self)
    return wrapped_test


def run_all_tests(pattern='*_test.py'):
    """This loads and runs all tests in scoreboard.tests."""
    if os.getenv("DEBUG_TESTS"):
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        logging.getLogger().setLevel(logging.INFO)
    test_dir = os.path.dirname(os.path.realpath(__file__))
    top_dir = os.path.abspath(os.path.join(test_dir, '..'))
    suite = unittest.defaultTestLoader.discover(
            test_dir, pattern=pattern,
            top_level_dir=top_dir)
    result = unittest.TextTestRunner().run(suite)
    return result.wasSuccessful()


def json_monkeypatch():
    """Automatically strip our XSSI header."""
    def new_loads(data, *args, **kwargs):
        try:
            prefix = utils.to_bytes(")]}',\n")
            if data.startswith(prefix):
                data = data[len(prefix):]
            return json.loads(data, *args, **kwargs)
        except Exception as exc:
            logging.exception('JSON monkeypatch failed: %s', exc)
    flask.json.loads = new_loads


json_monkeypatch()
