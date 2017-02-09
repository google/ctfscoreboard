#!/bin/bash

# stash code not to be committed
git stash -q --keep-index >/dev/null 2>&1

RESULT=0

if git ls-files -m . | grep -q '^scoreboard/' ; then
  # Run tests and flake8 if any files in scoreboard/... changed.
  python main.py runtests && flake8 .
  RESULT=$?
fi

# restore stash
git stash pop -q >/dev/null 2>&1

exit $RESULT
