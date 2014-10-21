# Copyright 2014 David Tomaschik <david@systemoverlord.com>
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

from app import app
import models
import rest
import views

# Imported just for views
modules_for_views = (rest, views)

if __name__ == '__main__':
    if 'createdb' in sys.argv:
        models.db.create_all()
    else:
        app.run(host='0.0.0.0', debug=True, port=app.config['PORT'])
