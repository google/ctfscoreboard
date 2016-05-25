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


from flask.ext import sqlalchemy
from flask.ext import testing
from scoreboard import app
from scoreboard import models


class BaseTestCase(TestCase):
    """Base TestCase for scoreboard.

    Monkey-patches the app and db objects.
    """

    SQLALCHEMY_DATABASE_URI = "sqlite://"
    TESTING = True

    def create_app(self):
        app.app = app.create_app(self)
        return app.app

    def setUp(self):
        self.app = app.app
        models.db = sqlalchemy.SQLAlchemy(app)
        models.db.create_all()

    def tearDown(self):
        models.db.session.remove()
        models.db.drop_all()
