## CTF Scoreboard ##

This is a basic CTF Scoreboard, with support for teams or individual
competitors, and a handful of other features.

Copyright 2020 Google LLC.
This is not an official Google product.

Author: Please see the AUTHORS file.

This is a version 2.x branch.  We've eliminated categories, in favor of tagging
challenges.  This simplifies the codebase significantly, and is a better fit
since so many challenges border on more than one category.  However, this branch
is not compatible with databases from 1.x.  If you need that, check out the 1.x
branch, which will only be getting security & bug fixes.

### Installation ###

1. Install Python with PIP and setuptools.  If you'd like to use a virtualenv,
   set one up and activate it now.  Please note that only Python 3.6+ is
   officially supported at the present time, but it should still work on Python 2.7.

2. Install the dependencies:
   pip install -r requirements.txt

3. Install a database library.  For MySQL, consider PyMySQL.  For Postgres,
   use psycopg2.  (Others may work; untested.)

4. Write a config.py for your relevant installation.  An example is provided in
   config.example.py.

        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://username:password@server/db'
        #SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://username:password@server/db'
        SECRET_KEY = 'Some Random Value For Session Keys'
        TEAM_SECRET_KEY = 'Another Random Value For Team Invite Codes'
        TITLE = 'FakeCTF'
        TEAMS = True
        ATTACHMENT_DIR = 'attachments'
        LOGIN_METHOD = 'local'  # or appengine

  If you are using plaintext HTTP to run your scoreboard, you will need to add the
  following to your config.py, so that cookies will work:

        SESSION_COOKIE_SECURE = False

  If you are developing the scoreboard, the following settings may be useful for
  debugging purposes. Not useful for production usage, however.

        COUNT_QUERIES = True
        SQLALCHEMY_ECHO = True

5. Create the database:

        python main.py createdb

6. Set up your favorite python application server, optionally behind a
   webserver.  You'll want to use main.app as your WSGI handler.
   Tested with uwsgi + nginx.  Not tested with anything else,
   let me know if you have success.  Sample configs are in doc/.

7. Register a user.  The first user registed is automatically made an admin.
   You probably want to register your user before your players get access.

8. Have fun!  Maybe set up some challenges.  Players might like that more.


### Installation using Docker ###

1. Navigate to the folder where the Dockerfile is located.

2. Run the command below to build a docker image for the scoreboard and tag it as "scoreboard".

       docker build -t "scoreboard" .

3. Run the command below to create the docker container.

       docker create -p 80:80 scoreboard

4. Find the name of the container you created for the scoreboard.

       docker container ls -a

5. Run the command below to start the docker container for the scoreboard.

       docker start "container_name"

### Options ###

**SCORING**: Set to 'progressive' to enable a scoring system where the total
points for each challenge are divided amongst all the teams that solve that
challenge.  This rewards teams that solve infrequently solved (hard or obscure)
challenges.

**TITLE**: Scoreboard page titles.

**TEAMS**: True if teams should be used, False for each player on their own
team.

**SQLALCHEMY_DATABASE_URI**: A SQLAlchemy database URI string.

**LOGIN_METHOD**: Supports 'local'

### Development ###

[![Build Status](https://travis-ci.org/google/ctfscoreboard.svg?branch=master)](https://travis-ci.org/google/ctfscoreboard)
[![codecov](https://codecov.io/gh/google/ctfscoreboard/branch/master/graph/badge.svg)](https://codecov.io/gh/google/ctfscoreboard)

**Use hooks**

    ln -s ../../.hooks/pre-commit.sh .git/hooks/pre-commit

**Test Cases**

- Setup database
- Create user, verify admin
- Create challenge
  - With, without attachment
- Edit challenges
  - Add attachment
  - Delete attachment
- Download backup
- Restore backup
- Create 2nd user, verify not admin
  - Solve challenge
  - Download attachment


### Thanks ###

This project stands on the shoulders of giants.
A big thanks to the following projects used to build this:

- [Flask](http://flask.pocoo.org/)
- [Flask-SQLAlchemy](https://pythonhosted.org/Flask-SQLAlchemy/)
- [Flask-RESTful](https://flask-restful.readthedocs.io/en/latest/)
- [SQLAlchemy](http://www.sqlalchemy.org/)
- [AngularJS](https://angularjs.org/)
- [jQuery](https://jquery.com/)
- [PageDown](https://jquery.com/)
- [Bootstrap](http://getbootstrap.com/)

And many more indirect dependencies.
