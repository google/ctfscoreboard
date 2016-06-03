# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

from scoreboard.app import app
from scoreboard import models
from scoreboard import rest
from scoreboard import views

# Imported just for views
modules_for_views = (rest, views)

if __name__ == '__main__':
    if 'createdb' in sys.argv:
        models.db.create_all()
    elif 'createdata' in sys.argv:
        from scoreboard.tests import data
        models.db.create_all()
        data.create_all()
    elif 'runtests' in sys.argv:
        from scoreboard.tests.utils_test import test_all
        test_all()
        print "All Tests Pass"
    else:
        app.run(host='0.0.0.0', debug=True, port=app.config.get('PORT', 9999))
