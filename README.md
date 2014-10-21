PwnableWeb Scoreboard

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

5. Create the database:

        python main.py createdb

6. Set up your favorite python application server, optionally behind a
   webserver.  Tested with uwsgi + nginx.  Not tested with anything else,
   let me know if you have success.

7. Register a user.  The first user registed is automatically made an admin.
   You probably want to register your user before your players get access.

8. Have fun!  Maybe set up some challenges.  Players might like that more.
