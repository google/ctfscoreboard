#!/bin/bash

# stash code not to be committed
git stash -q -keep-index

# Run tests and flake8
python main.py runtests && flake8 .
RESULT=$?

# restore stash
git stash pop -q

exit $RESULT
