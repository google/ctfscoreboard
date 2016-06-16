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
import StringIO

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

class AttachmentTest(base.RestTestCase):

    PATH = '/api/attachment/%s'
    ATTACHMENT_FIELDS = ('aid', 'filename', 'challenges')

    text = "This is a test"
    name = "test.txt"

    def uploadFile(self, filename, text):
        with self.admin_client as c:
            string = StringIO.StringIO()
            string.write(text)
            string.seek(0)
            return c.post('/api/attachment', data = {
                'file': (string, filename)
            })

    def fetchFile(self, aid):
        with self.admin_client as c:
            return c.get(self.PATH % aid)

    def testUploadFile(self):
        resp = self.uploadFile("test.txt", "This is a test")
        self.assert200(resp)
        #Calculated using an external sha256 tool
        self.assertEquals(resp.json['aid'], "c7be1ed902fb8dd4d48997c6452f5d7e509fbcdbe2808b16bcf4edce4c07d14e")

    def testQueryFile(self):
        postresp = self.uploadFile(self.name, self.text)
        getresp = self.fetchFile(postresp.json['aid'])
        self.assert200(getresp)

    def testFileQueryAID(self):
        postresp = self.uploadFile(self.name, self.text)
        getresp = self.fetchFile(postresp.json['aid'])
        self.assertEqual(getresp.json['aid'], postresp.json['aid'])

    def testFileQueryName(self):
        postresp = self.uploadFile(self.name, self.text)
        getresp = self.fetchFile(postresp.json['aid'])
        self.assertEqual(getresp.json['filename'], self.name)

    def testFileChallengesEmpty(self):
        postresp = self.uploadFile(self.name, self.text)
        getresp = self.fetchFile(postresp.json['aid'])
        self.assertEqual(len(getresp.json['challenges']), 0)

    def testRetrieveFile(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            getresp = c.get('/attachment/%s' % postresp.json['aid'])
            self.assert200(getresp)

    def testFileRetrievalValue(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            getresp = c.get('/attachment/%s' % postresp.json['aid'])
            self.assertEqual(getresp.get_data(), self.text)

    def testFileDelete(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            delresp = c.delete('/api/attachment/%s' % postresp.json['aid'])
            self.assert200(delresp)

    def testDeletionRemovesFile(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            delresp = c.delete('/api/attachment/%s' % postresp.json['aid'])
        with self.admin_client as c:
            getresp = c.get('/api/attachment/%s' % postresp.json['aid'])
            self.assert404(getresp)

    def testFileUpdate(self):
        new_name = "file.png"
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            putresp = c.put('/api/attachment/%s' % postresp.json['aid'], data = json.dumps({
                'filename': new_name,
                'aid': postresp.json['aid'],
                'challenges': [],
            }), content_type = "application/json")
            self.assert200(putresp)

    def testUpdateChangesName(self):
        new_name = "file.png"
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            putresp = c.put('/api/attachment/%s' % postresp.json['aid'], data = json.dumps({
                'filename': new_name,
                'aid': postresp.json['aid'],
                'challenges': [],
            }), content_type = "application/json")
        with self.admin_client as c:
            getresp = c.get('/api/attachment/%s' % postresp.json['aid'])
            self.assertEqual(getresp.json['filename'], new_name)

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

    def testUpdateUserNoAccess(self):
        user = self.admin_client.user
        with self.authenticated_client as c:
            data = {'password': 'hunter3'}
            self.assert403(c.put(self.PATH % user.uid,
                data=json.dumps(data), content_type='application/json'))

    def testUpdateUserAdmin(self):
        user = self.authenticated_client.user
        with self.admin_client as c:
            data = {'nick': 'Lame'}
            resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertEqual('Lame', resp.json['nick'])

    def testUpdateUserPromote(self):
        user = self.authenticated_client.user
        with self.admin_client as c:
            data = {'nick': user.nick, 'admin': True}
            resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertTrue(resp.json['admin'])

    def testUpdateUserDemote(self):
        user = self.admin_client.user
        with self.admin_client as c:
            data = {'nick': user.nick, 'admin': False}
            resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertFalse(resp.json['admin'])

    def testUpdateUserNoSelfPromotion(self):
        user = self.authenticated_client.user
        with self.authenticated_client as c:
            data = {'admin': True}
            resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertFalse(resp.json['admin'])

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

    @staticmethod
    def default_data():
        return {
            'email': 'test@example.com',
            'nick': 'test3',
            'password': 'test3',
            'team_id': 'new',
            'team_name': 'New Team',
            'team_code': None,
        }

    def testRegisterUser(self):
        data = self.default_data()
        with self.client as c:
            resp = c.post('/api/users', data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertItemsEqual(self.USER_FIELDS, resp.json.keys())
            self.assertEqual(resp.json['uid'], flask.session['user'])
            self.assertEqual(resp.json['admin'], flask.session['admin'])
            self.assertEqual(resp.json['team_tid'], flask.session['team'])

    def testRegisterUserTeam(self):
        team = self.authenticated_client.team
        data = self.default_data()
        data.update({
            'team_id': team.tid,
            'team_name': None,
            'team_code': team.code,
        })
        with self.client as c:
            resp = c.post('/api/users', data=json.dumps(data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertItemsEqual(self.USER_FIELDS, resp.json.keys())
            self.assertEqual(resp.json['uid'], flask.session['user'])
            self.assertEqual(resp.json['admin'], flask.session['admin'])
            self.assertEqual(resp.json['team_tid'], flask.session['team'])
            self.assertEqual(team.tid, resp.json['team_tid'])

    def testRegisterUserTeamNoCode(self):
        team = self.authenticated_client.team
        data = self.default_data()
        data.update({
            'team_id': team.tid,
            'team_name': None,
            'team_code': 'xxx',
        })
        with self.client as c:
            resp = c.post('/api/users', data=json.dumps(data),
                    content_type='application/json')
            self.assert400(resp)

    def testRegisterUserLoggedInFails(self):
        data = self.default_data()
        with self.authenticated_client as c:
            resp = c.post('/api/users', data=json.dumps(data),
                    content_type='application/json')
            self.assert400(resp)

    def testRegisterUserNoNick(self):
        data = self.default_data()
        del data['nick']
        self.assert400(self.client.post('/api/users',
            data=json.dumps(data), content_type='application/json'))

    def testRegisterUserNoTeam(self):
        data = self.default_data()
        del data['team_name']
        del data['team_id']
        self.assert400(self.client.post('/api/users',
            data=json.dumps(data), content_type='application/json'))
