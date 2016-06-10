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


import flask

from scoreboard.tests import base
from scoreboard import models
from scoreboard import rest


class ConfigzTest(base.RestTestCase):

    PATH = '/api/configz'

    def testGetAnonymous(self):
        response = self.client.get(self.PATH)
        self.assert403(response)

    def testGetNonAdmin(self):
        with self.authenticated_client as c:
            response = self.client.get(self.PATH)
            self.assert403(response)

    def testAdmin(self):
        with self.admin_client as c:
            response = c.get(self.PATH)
            self.assert200(response)


class PageTest(base.RestTestCase):

    PATH = '/api/page/home'

    def testGetAnonymous(self):
        page = models.Page()
        page.path = 'home'
        page.title = 'Home'
        page.contents = 'Home Page'
        models.db.session.add(page)
        models.db.session.commit()
        response = self.client.get(self.PATH)
        self.assert200(response)
        self.assertEqual(page.title, response.json['title'])
        self.assertEqual(page.contents, response.json['contents'])

    def testGetNonExistent(self):
        self.assert404(self.client.get(self.PATH))
