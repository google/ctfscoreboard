#!/bin/bash

# stash code not to be committed
git stash -q --keep-index >/dev/null 2>&1

# Run tests and flake8
python main.py runtests && flake8 .
RESULT=$?

# restore stash
git stash pop -q >/dev/null 2>&1

exit $RESULT
