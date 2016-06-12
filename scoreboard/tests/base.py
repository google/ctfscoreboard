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

"""Base test module, MUST be imported first."""

import json
import logging
import os.path
import unittest

import flask
import flask_sqlalchemy
import flask_testing
from sqlalchemy import event

from scoreboard import main
from scoreboard import models


class BaseTestCase(flask_testing.TestCase):
    """Base TestCase for scoreboard.

    Monkey-patches the app and db objects.
    """

    TEST_CONFIG = dict(
        PRESERVE_CONTEXT_ON_EXCEPTION = False,
        SECRET_KEY = 'testing-session-key',
        SQLALCHEMY_DATABASE_URI = "sqlite://",
        TEAMS = True,
        TESTING = True,
    )

    def create_app(self):
        app = main.get_app()
        app.config.update(self.TEST_CONFIG)
        main.setup_logging(app)
        return app

    def setUp(self):
        """Re-setup the DB to ensure a fresh instance."""
        super(BaseTestCase, self).setUp()
        models.db.init_app(main.get_app())
        models.db.create_all()

    def tearDown(self):
        models.db.session.remove()
        models.db.drop_all()
        super(BaseTestCase, self).tearDown()

    def queryLimit(self, limit=None):
        return MaxQueryBlock(limit)


class RestTestCase(BaseTestCase):
    """Special features for testing rest handlers."""

    def setUp(self):
        super(RestTestCase, self).setUp()
        self.admin_client = AdminClient(self.client)
        self.authenticated_client = AuthenticatedClient(self.client)

    def tearDown(self):
        super(RestTestCase, self).tearDown()


class AuthenticatedClient(object):
    """Like TestClient, but authenticated."""

    def __getattr__(self, attr):
        return getattr(self.client, attr)

    def __init__(self, client):
        self.client = client
        self.team = models.Team.create('team')
        self.user = models.User.create('auth@example.com', 'Authenticated',
                'hunter2', team=self.team)
        models.db.session.commit()
        self.uid = self.user.uid
        self.tid = self.team.tid

    def __enter__(self):
        rv = self.client.__enter__()
        with rv.session_transaction() as sess:
            sess['user'] = self.uid
            sess['team'] = self.tid
        return rv

    def __exit__(self, *args, **kwargs):
        return self.client.__exit__(*args, **kwargs)


class AdminClient(AuthenticatedClient):
    """Like TestClient, but admin."""

    def __init__(self, client):
        self.client = client
        self.user = models.User.create('admin@example.com', 'Admin', 'hunter2')
        self.user.admin = True
        models.db.session.commit()
        self.uid = self.user.uid

    def __enter__(self):
        rv = self.client.__enter__()
        with rv.session_transaction() as sess:
            sess['user'] = self.uid
            sess['admin'] = True
        return rv


class MaxQueryBlock(object):
    """Run a certain block with a maximum number of queries."""

    def __init__(self, max_count=None):
        self.max_count = max_count
        self.queries = []
        self._sql_listen_args = (models.db.engine, 'before_cursor_execute',
                self._count_query)

    def __enter__(self):
        event.listen(*self._sql_listen_args)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        event.remove(*self._sql_listen_args)
        if exc_type is not None:
            return False
        if self.max_count is None:
            return
        if len(self.queries) > self.max_count:
            message = ('Maximum query count exceeded: limit %d, executed %d.\n'
                       '----QUERIES----\n%s\n----END----') % (
                            self.max_count, len(self.queries), '\n'.join(self.queries))
            raise AssertionError(message)

    def _count_query(self, unused_conn, unused_cursor, statement, parameters,
            unused_context, unused_executemany):
        statement = '%s (%s)' % (statement, ', '.join(str(x) for x in parameters))
        self.queries.append(statement)
        logging.debug('SQLAlchemy: %s', statement)


def run_all_tests():
    """This loads and runs all tests in scoreboard.tests."""
    logging.getLogger().setLevel(logging.INFO)
    test_dir = os.path.dirname(os.path.realpath(__file__))
    top_dir = os.path.abspath(os.path.join(test_dir, '..'))
    suite = unittest.defaultTestLoader.discover(test_dir, pattern='*_test.py',
            top_level_dir=top_dir)
    unittest.TextTestRunner().run(suite)


def json_monkeypatch():
    """Automatically strip our XSSI header."""
    def new_loads(data, *args, **kwargs):
        try:
            prefix = ")]}',\n"
            if data.startswith(prefix):
                data = data[len(prefix):]
            return json.loads(data, *args, **kwargs)
        except Exception as exc:
            logging.exception('JSON monkeypatch failed: ', exc)
    flask.json.loads = new_loads

json_monkeypatch()
