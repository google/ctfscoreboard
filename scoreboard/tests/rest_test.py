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


def makeTestUser():
    u = models.User.create('email@example.com', 'Nick', 'hunter2')
    models.db.session.commit()
    return u

def makeTestTeam(user):
    t = models.Team.create('Test')
    user.team = t
    models.db.session.commit()
    return t


class ConfigzTest(base.RestTestCase):

    PATH = '/api/configz'

    def testGetAnonymous(self):
        with self.queryLimit(0):
            response = self.client.get(self.PATH)
        self.assert403(response)

    def testGetNonAdmin(self):
        with self.authenticated_client as c:
            with self.queryLimit(0):
                response = self.client.get(self.PATH)
            self.assert403(response)

    def testAdmin(self):
        with self.admin_client as c:
            with self.queryLimit(0):
                response = c.get(self.PATH)
            self.assert200(response)


class PageTest(base.RestTestCase):

    PATH = '/api/page/home'
    PATH_NEW = '/api/page/new'
    PATH_404 = '/api/page/404'

    def setUp(self):
        super(PageTest, self).setUp()
        page = models.Page()
        page.path = 'home'
        page.title = 'Home'
        page.contents = 'Home Page'
        models.db.session.add(page)
        models.db.session.commit()
        self.page = page

    def testGetAnonymous(self):
        with self.queryLimit(1):
            response = self.client.get(self.PATH)
        self.assert200(response)
        self.assertEqual(self.page.title, response.json['title'])
        self.assertEqual(self.page.contents, response.json['contents'])

    def testGetNonExistent(self):
        with self.queryLimit(1):
            self.assert404(self.client.get(self.PATH_404))

    def testDeletePage(self):
        with self.admin_client as c:
            self.assert200(c.get(self.PATH))
            with self.queryLimit(1):
                self.assert200(c.delete(self.PATH))
            self.assert404(c.get(self.PATH))

    def testCreatePage(self):
        with self.admin_client as c:
            page_data = dict(
                 title='Test',
                 contents='Test Page Contents',
                 )
            with self.queryLimit(3):
                resp = c.post(self.PATH_NEW, data=json.dumps(page_data),
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
            with self.queryLimit(0):
                resp = c.post(self.PATH_NEW, data=json.dumps(page_data),
                        content_type='application/json')
            self.assert403(resp)

    def testUpdatePage(self):
        with self.admin_client as c:
            page_data = dict(
                 title='Test',
                 contents='Test Page Contents',
                 )
            with self.queryLimit(3):
                resp = c.post(self.PATH, data=json.dumps(page_data),
                    content_type='application/json')
            self.assert200(resp)
            self.assertEqual(page_data['title'], resp.json['title'])
            self.assertEqual(page_data['contents'], resp.json['contents'])


class UserTest(base.RestTestCase):

    PATH = '/api/users/%d'
    USER_FIELDS = ('admin', 'nick', 'email', 'team_tid', 'uid')

    def testGetAnonymous(self):
        path = self.PATH % makeTestUser().uid
        with self.queryLimit(0):
            self.assert403(self.client.get(path))

    def testGetNonExistentAnonymous(self):
        path = self.PATH % 999
        with self.queryLimit(0):
            self.assert403(self.client.get(path))

    def testGetNonExistentAuth(self):
        path = self.PATH % 999
        with self.authenticated_client as c:
            with self.queryLimit(0):
                resp = c.get(path)
            self.assert403(resp)
            self.assertIn("No access", resp.json['message'])

    def testGetNonExistentAdmin(self):
        path = self.PATH % 999
        with self.admin_client as c:
            with self.queryLimit(1):
                resp = c.get(path)
            self.assert404(resp)

    def testGetSelf(self):
        user = self.authenticated_client.user
        with self.authenticated_client as c:
            with self.queryLimit(1):
                resp = c.get(self.PATH % user.uid)
            self.assert200(resp)
            self.assertEqual(user.email, resp.json['email'])
            self.assertEqual(user.nick, resp.json['nick'])
            self.assertEqual(user.admin, resp.json['admin'])

    def testUpdateUser(self):
        user = self.authenticated_client.user
        with self.authenticated_client as c:
            data = {'password': 'hunter3'} # for security
            with self.queryLimit(2):
                self.assert200(c.put(self.PATH % user.uid,
                    data=json.dumps(data), content_type='application/json'))

    def testUpdateUserNoAccess(self):
        uid = self.admin_client.user.uid
        with self.authenticated_client as c:
            data = {'password': 'hunter3'}
            with self.queryLimit(0):
                resp = c.put(self.PATH % uid,
                    data=json.dumps(data), content_type='application/json')
                self.assert403(resp)

    def testUpdateUserAdmin(self):
        uid = self.authenticated_client.user.uid
        with self.admin_client as c:
            data = {'nick': 'Lame'}
            with self.queryLimit(2):
                resp = c.put(self.PATH % uid, data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertEqual('Lame', resp.json['nick'])
            self.assertNotEqual('Lame',
                    self.authenticated_client.user.team.name)

    def testUpdateUsersNoTeams(self):
        uid = self.authenticated_client.user.uid
        self.app.config['TEAMS'] = False
        with self.admin_client as c:
            data = {'nick': 'Lame'}
            with self.queryLimit(3):
                resp = c.put(self.PATH % uid, data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertEqual('Lame', resp.json['nick'])
            self.assertEqual('Lame', self.authenticated_client.user.team.name)

    def testUpdateUserPromote(self):
        user = self.authenticated_client.user
        with self.admin_client as c:
            data = {'nick': user.nick, 'admin': True}
            # yes, this is a lot, but promoting is infrequent
            with self.queryLimit(7):
                resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertTrue(resp.json['admin'])

    def testUpdateUserDemote(self):
        user = self.admin_client.user
        with self.admin_client as c:
            data = {'nick': user.nick, 'admin': False}
            with self.queryLimit(3):
                resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertFalse(resp.json['admin'])

    def testUpdateUserNoSelfPromotion(self):
        uid = self.authenticated_client.user.uid
        with self.authenticated_client as c:
            data = {'admin': True}
            with self.queryLimit(1):
                resp = c.put(self.PATH % uid, data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertFalse(resp.json['admin'])

    def testUpdateUserNoAnswers(self):
        user = self.authenticated_client.user
        team = self.authenticated_client.user.team
        chall = models.Challenge.create('Foo', 'Foo', 1, 'Foo', 'foo')
        answer = models.Answer.create(chall, team, 'Foo')
        models.db.session.commit()
        with self.admin_client as c:
            data = {'nick': user.nick, 'admin': True}
            with self.queryLimit(3):
                resp = c.put(self.PATH % user.uid, data=json.dumps(data),
                        content_type='application/json')
            self.assert400(resp)
            user = models.User.query.get(user.uid)
            self.assertFalse(user.admin)

    def testGetUsersNoAccess(self):
        with self.authenticated_client as c:
            with self.queryLimit(0):
                resp = c.get('/api/users')
            self.assert403(resp)

    def testGetUsers(self):
        user = self.admin_client.user
        with self.admin_client as c:
            with self.queryLimit(1):
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

    def testRegisterUserNewTeam(self):
        data = self.default_data()
        with self.client as c:
            # TODO: maybe optimize?
            with self.queryLimit(9):
                resp = c.post('/api/users', data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertItemsEqual(self.USER_FIELDS, resp.json.keys())
            self.assertEqual(resp.json['uid'], flask.session['user'])
            self.assertEqual(resp.json['admin'], flask.session['admin'])
            self.assertEqual(resp.json['team_tid'], flask.session['team'])

    def testRegisterUserExistingTeam(self):
        team = self.authenticated_client.team
        data = self.default_data()
        data.update({
            'team_id': team.tid,
            'team_name': None,
            'team_code': team.code,
        })
        with self.client as c:
            with self.queryLimit(8):
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
            with self.queryLimit(1):
                resp = c.post('/api/users', data=json.dumps(data),
                        content_type='application/json')
            self.assert400(resp)

    def testRegisterUserLoggedInFails(self):
        data = self.default_data()
        with self.authenticated_client as c:
            with self.queryLimit(0):
                resp = c.post('/api/users', data=json.dumps(data),
                        content_type='application/json')
            self.assert400(resp)

    def testRegisterUserNoNick(self):
        data = self.default_data()
        del data['nick']
        with self.queryLimit(0):
            self.assert400(self.client.post('/api/users',
                data=json.dumps(data), content_type='application/json'))

    def testRegisterUserNoTeam(self):
        data = self.default_data()
        del data['team_name']
        del data['team_id']
        with self.queryLimit(0):
            self.assert400(self.client.post('/api/users',
                data=json.dumps(data), content_type='application/json'))


class TeamTest(base.RestTestCase):

    LIST_URL = '/api/teams'

    def setUp(self):
        super(TeamTest, self).setUp()
        self.user = makeTestUser()
        self.team = makeTestTeam(self.user)
        self.team_path = '/api/teams/%d' % self.team.tid

    def testGetTeam(self):
        with self.authenticated_client as c:
            with self.queryLimit(4):
                resp = c.get(self.team_path)
            self.assert200(resp)
            self.assertEqual(0, len(resp.json['players']))
            self.assertEqual(self.team.name, resp.json['name'])
            # TODO: check other fields

    def testGetTeamAnonymous(self):
        with self.client as c:
            with self.queryLimit(0):
                self.assert403(c.get(self.team_path))

    def testGetTeamAdmin(self):
        with self.admin_client as c:
            with self.queryLimit(4):
                resp = c.get(self.team_path)
            self.assert200(resp)
            self.assertEqual(1, len(resp.json['players']))

    def testUpdateTeamAdmin(self):
        data = {'name': 'Updated'}
        with self.admin_client as c:
            with self.queryLimit(6):
                resp = c.put(self.team_path, data=json.dumps(data),
                        content_type='application/json')
            self.assert200(resp)
            self.assertEqual('Updated', resp.json['name'])
        team = models.Team.query.get(self.team.tid)
        self.assertEqual('Updated', team.name)

    def testGetTeamList(self):
        with self.client as c:
            with self.queryLimit(3) as ctr:
                resp = c.get(self.LIST_URL)
                n_queries = ctr.query_count
            self.assert200(resp)
            models.Team.create('Test 2')
            models.Team.create('Test 3')
            models.Team.create('Test 4')
            models.db.session.commit()
            with self.queryLimit(n_queries):
                resp = c.get(self.LIST_URL)
            self.assert200(resp)
