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
