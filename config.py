# Demo config.py, please configure your own
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://scoreboard:pass123word@localhost/scoreboard'
SECRET_KEY = 'CHANGEME CHANGEME CHANGEME'
TITLE = 'CTF Scoreboard Dev'
TEAMS = True
ATTACHMENT_BACKEND = 'file:///tmp/attachments'
LOGIN_METHOD = 'appengine'
