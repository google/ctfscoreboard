## CTF Scoreboard ##

This is a basic CTF Scoreboard, with support for hints, teams or individual
competitors, and a handful of other features.

Author: David Tomaschik <david@systemoverlord.com>

### Installation ###
1. Install Python with PIP and setuptools.  If you'd like to use a virtualenv,
   set one up and activate it now.

2. Install the dependencies:
   pip install -r requirements.txt

3. Install a database library.  For MySQL, consider mysql-python.  For Postgres,
   use psycopg2.  (Others may work; untested.)

4. Write a config.py for your relevant installation.

        SQLALCHEMY_DATABASE_URI = 'mysql://username:password@server/db'
        #SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://username:password@server/db'
        SECRET_KEY = 'Some Random Value For Session Keys'
        TITLE = 'FakeCTF'
        TEAMS = True
        ATTACHMENT_DIR = 'attachments'
        LOGIN_METHOD = 'local'  # or appengine

5. Create the database:

        python main.py createdb

6. Set up your favorite python application server, optionally behind a
   webserver.  You'll want to use main.app as your WSGI handler.
   Tested with uwsgi + nginx.  Not tested with anything else,
   let me know if you have success.  Sample configs are in doc/.

7. Register a user.  The first user registed is automatically made an admin.
   You probably want to register your user before your players get access.

8. Have fun!  Maybe set up some challenges.  Players might like that more.

### Options ###

**SCORING**: Set to 'progressive' to enable a scoring system where the total
points for each challenge are divided amongst all the teams that solve that
challenge.  This rewards teams that solve infrequently solved (hard or obscure)
challenges.

**TITLE**: Scoreboard page titles.

**TEAMS**: True if teams should be used, False for each player on their own
team.

**SQLALCHEMY_DATABASE_URI**: A SQLAlchemy database URI string.

**LOGIN_METHOD**: Supports 'local' or 'appengine'.  'appengine' uses AppEngine
users API.

### Development ###

**Test Cases**

- Setup database
- Create user, verify admin
- Create category
- Create challenge
  - With, without hint
  - With, without attachment
- Edit challenges
  - Add attachment
  - Delete attachment
  - Add hint
  - Delete hint
- Download backup
- Restore backup
- Create 2nd user, verify not admin
  - Solve challenge
  - Download attachment
  - Get hint
  - Solve challenge w/hint


### Thanks ###

This project stands on the shoulders of giants.
A big thanks to the following projects used to build this:

- [Flask](http://flask.pocoo.org/)
- [Flask-SQLAlchemy](https://pythonhosted.org/Flask-SQLAlchemy/)
- [Flask-RESTful](http://flask-restful.readthedocs.org/en/latest/)
- [SQLAlchemy](http://www.sqlalchemy.org/)
- [AngularJS](https://angularjs.org/)
- [jQuery](https://jquery.com/)
- [PageDown](https://jquery.com/)
- [Bootstrap](http://getbootstrap.com/)

And many more indirect dependencies.
