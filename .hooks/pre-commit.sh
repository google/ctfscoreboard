#!/bin/bash

if [ "${SKIP_TESTS}" != "" ] ; then
    exit 0
fi

# stash code not to be committed
git stash -q --keep-index >/dev/null 2>&1

RESULT=0

if git status --porcelain | awk '{print $2}' | grep -q '^scoreboard/' ; then
  # Run tests and flake8 if any files in scoreboard/... changed.
  python main.py runtests && flake8 scoreboard main.py
  RESULT=$?
fi

# restore stash
# git has a bad bug with 2.24 and --quiet where it deletes files
if git --version | grep -q '^git version 2.24' ; then
    git stash pop >/dev/null 2>&1
else
    git stash pop -q >/dev/null 2>&1
fi

exit $RESULT
