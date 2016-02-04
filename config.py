# Demo config.py, please configure your own
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/scoreboard.db'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SECRET_KEY = 'CHANGEME CHANGEME CHANGEME'
TITLE = 'CTF Scoreboard Dev'
TEAMS = True
ATTACHMENT_BACKEND = 'file:///tmp/attachments'
LOGIN_METHOD = 'local'
