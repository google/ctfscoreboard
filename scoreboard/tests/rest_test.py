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
import json

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

    @staticmethod
    def makeTestPage():
        page = models.Page()
        page.path = 'home'
        page.title = 'Home'
        page.contents = 'Home Page'
        models.db.session.add(page)
        models.db.session.commit()
        return page

    def testGetAnonymous(self):
        page = self.makeTestPage()
        response = self.client.get(self.PATH)
        self.assert200(response)
        self.assertEqual(page.title, response.json['title'])
        self.assertEqual(page.contents, response.json['contents'])

    def testGetNonExistent(self):
        self.assert404(self.client.get(self.PATH))

    def testDeletePage(self):
        page = self.makeTestPage()
        with self.admin_client as c:
            self.assert200(c.get(self.PATH))
            self.assert200(c.delete(self.PATH))
            self.assert404(c.get(self.PATH))

    def testCreatePage(self):
        with self.admin_client as c:
            page_data = dict(
                 title='Test',
                 contents='Test Page Contents',
                 )
            resp = c.post(self.PATH, data=json.dumps(page_data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertEqual(page_data['title'], resp.json['title'])
            self.assertEqual(page_data['contents'], resp.json['contents'])

    def testCreatePageNonAdmin(self):
        with self.authenticated_client as c:
            page_data = dict(
                 title='Test',
                 contents='Test Page Contents',
                 )
            resp = c.post(self.PATH, data=json.dumps(page_data),
                    content_type='application/json')
            self.assert403(resp)


class UserTest(base.RestTestCase):

    PATH = '/api/users/%d'
    USER_FIELDS = ('admin', 'nick', 'email', 'team_tid', 'uid')

    def makeTestUser(self):
        u = models.User.create('email@example.com', 'Nick', 'hunter2')
        models.db.session.commit()
        return u

    def testGetAnonymous(self):
        path = self.PATH % self.makeTestUser().uid
        self.assert403(self.client.get(path))

    def testGetNonExistentAnonymous(self):
        path = self.PATH % 999
        self.assert403(self.client.get(path))

    def testGetNonExistentAuth(self):
        path = self.PATH % 999
        with self.authenticated_client as c:
            resp = c.get(path)
            self.assert403(resp)
            self.assertIn("No access", resp.json['message'])

    def testGetNonExistentAdmin(self):
        path = self.PATH % 999
        with self.admin_client as c:
            resp = c.get(path)
            self.assert404(resp)

    def testGetSelf(self):
        user = self.authenticated_client.user
        with self.authenticated_client as c:
            resp = c.get(self.PATH % user.uid)
            self.assert200(resp)
            self.assertEqual(user.email, resp.json['email'])
            self.assertEqual(user.nick, resp.json['nick'])
            self.assertEqual(user.admin, resp.json['admin'])

    def testUpdateUser(self):
        user = self.authenticated_client.user
        with self.authenticated_client as c:
            data = {'password': 'hunter3'} # for security
            self.assert200(c.put(self.PATH % user.uid,
                data=json.dumps(data), content_type='application/json'))

    def testUpdateUserAdmin(self):
        user = self.authenticated_client.user
        with self.admin_client as c:
            data = {'nick': 'Lame'}
            resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertEqual('Lame', resp.json['nick'])

    def testGetUsers(self):
        user = self.admin_client.user
        with self.admin_client as c:
            resp = c.get('/api/users')
            self.assert200(resp)
            self.assertIsInstance(resp.json, dict)
            self.assertIn('users', resp.json)
            self.assertIsInstance(resp.json['users'], list)
            users = resp.json['users']
            self.assertEqual(2, len(users))
            for u in users:
                self.assertItemsEqual(self.USER_FIELDS, u.keys())

    def testRegisterUser(self):
        data = {
            'email': 'test@example.com',
            'nick': 'test3',
            'password': 'test3',
            'team_id': 'new',
            'team_name': 'New Team',
            'team_code': None,
        }
        with self.client as c:
            resp = c.post('/api/users', data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertItemsEqual(self.USER_FIELDS, resp.json.keys())
            self.assertEqual(resp.json['uid'], flask.session['user'])
            self.assertEqual(resp.json['admin'], flask.session['admin'])
            self.assertEqual(resp.json['team_tid'], flask.session['team'])
