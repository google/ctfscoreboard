# Development Setup

You'll want to have `python3` and `pip` installed.  I also recommend
`virtualenv` and `virtualenvwrapper` (if you don't have these, skip the
virtualenv steps).

On Debian or Ubuntu Linux, run:

`apt install python3 python3-pip virtualenvwrapper`

1. `mkvirtualenv -p $(which python3) scoreboard` to create the virtualenv.
2. `git clone https://github.com/google/ctfscoreboard && cd ctfscoreboard` to clone the source.
3. `pip install -r requirements.txt` to install runtime dependencies.
4. `pip install -r doc/developing/requirements.txt` to install development
   dependencies.
5. `ln -s .hooks/pre-commit.sh .git/hooks/pre-commit` to install the development
   pre-commit hook.

# Configuration & Initial Setup

Copy the file `config.example.py` to `config.py` to make a configuration.  This
is suitable for basic development work, and will use a sqlite3 database in
`/tmp/scoreboard.db` for storage.

You'll want to run `python main.py createdb` to create the initial database.

Optionally, you can run `python main.py createdata` to create some test data.
These are just dummy challenges, teams, and users used for testing.

# Running/Iterating

You can either run `make dev` or `python main.py` to run the development server.
By default, it runs on port 9999, but you can change this in your `config.py`.

**Note** that if you make changes to models, affecting the database schema, you
must either manually update your database, or delete it and recreate from
scratch.  Because this is a CTF scoreboard, used for short-lived events, there's
no migration code.

Run `make scss` to compile SCSS to CSS.  You'll want to do this at least once,
and any time you change the SCSS.  Note that the CSS is not tracked in the git
repository, so all style changes *must* be to SCSS.

# Making Changes

Please do all development work on a feature branch.  Run the tests before you
commit (if you have the git hook, it should run the the tests before
committing).  We try to mostly follow PEP-8, and `flake8` helps catch those
mistakes.
