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
from scoreboard.tests import data
from scoreboard import models
from scoreboard import rest
from scoreboard import utils
from scoreboard import views

# Needed imports
_ = (rest, views)


def makeTestUser():
    u = models.User.create('email@example.com', 'Nick', 'hunter2')
    models.db.session.commit()
    return u


def makeTestTeam(user):
    t = models.Team.create('Test')
    user.team = t
    models.db.session.commit()
    return t


def makeTestChallenges():
    cats = data.make_categories()
    tags = data.make_tags()
    challs = data.make_challenges(cats, tags)
    models.db.session.commit()
    return challs, cats


class ConfigzTest(base.RestTestCase):

    PATH = '/api/configz'

    def testGetFails(self):
        with self.queryLimit(0):
            response = self.client.get(self.PATH)
        self.assert403(response)

    testGetFailsNonAdmin = base.authenticated_test(testGetFails)

    @base.admin_test
    def testAdmin(self):
        with self.queryLimit(0):
            response = self.client.get(self.PATH)
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

    @base.admin_test
    def testDeletePage(self):
        with self.client as c:
            self.assert200(c.get(self.PATH))
            with self.queryLimit(1):
                self.assert200(c.delete(self.PATH))
            self.assert404(c.get(self.PATH))

    @base.admin_test
    def testCreatePage(self):
        page_data = dict(
                title='Test',
                contents='Test Page Contents',
                )
        with self.queryLimit(3):
            resp = self.postJSON(self.PATH_NEW, page_data)
        self.assert200(resp)
        self.assertEqual(page_data['title'], resp.json['title'])
        self.assertEqual(page_data['contents'], resp.json['contents'])

    @base.authenticated_test
    def testCreatePageNonAdmin(self):
        page_data = dict(
                title='Test',
                contents='Test Page Contents',
                )
        with self.queryLimit(0):
            resp = self.postJSON(self.PATH_NEW, page_data)
        self.assert403(resp)

    @base.admin_test
    def testUpdatePage(self):
        page_data = dict(
                title='Test',
                contents='Test Page Contents',
                )
        with self.queryLimit(3):
            resp = self.postJSON(self.PATH, page_data)
        self.assert200(resp)
        self.assertEqual(page_data['title'], resp.json['title'])
        self.assertEqual(page_data['contents'], resp.json['contents'])


class UpdateTeam(base.RestTestCase):

    PATH = '/api/teams/change'

    _state = None

    def createTeam(self, teamname):
        team = models.Team.create(teamname)
        models.db.session.commit()
        return team

    def changeTeam(self, tid, code):
        return self.putJSON(self.PATH, {
            'uid': self.authenticated_client.uid,
            'team_tid': tid,
            'code': code
        })

    def patchState(self, time='BEFORE'):
        self._state = utils.GameTime.state
        utils.GameTime.state = staticmethod(lambda: time)

    def restoreState(self):
        if self._state:
            utils.GameTime.state = self._state

    @base.authenticated_test
    def testChangeTeam(self):
        self.patchState()
        test_team = self.createTeam('test')
        resp = self.changeTeam(test_team.tid, test_team.code)
        self.assert200(resp)
        self.restoreState()

    @base.authenticated_test
    def testTeamChangeWorked(self):
        self.patchState()
        test_team = self.createTeam('test2')
        self.changeTeam(test_team.tid, test_team.code)
        tid = self.authenticated_client.user.team.tid
        self.assertEqual(tid, test_team.tid)
        self.restoreState()

    @base.authenticated_test
    def testEmptyTeamIsDeleted(self):
        self.patchState()
        test_team_first = self.createTeam('first')
        test_team_second = self.createTeam('second')
        self.changeTeam(test_team_first.tid, test_team_first.code)
        self.changeTeam(test_team_second.tid, test_team_second.code)
        tid = self.authenticated_client.user.team.tid
        self.assertEqual(tid, test_team_second.tid)

        self.assertIsNone(models.Team.query.get(test_team_first.tid))
        self.restoreState()

    @base.authenticated_test
    def testTeamWithSolvesNotDeleted(self):
        self.patchState()
        test_team_first = self.createTeam('first')
        test_team_second = self.createTeam('second')
        self.changeTeam(test_team_first.tid, test_team_first.code)

        chall = models.Challenge.create('Foo', 'Foo', 1, 'Foo', 'foo')
        models.Answer.create(chall, test_team_first, 'Foo')

        self.changeTeam(test_team_second.tid, test_team_second.code)
        tid = self.authenticated_client.user.team.tid
        self.assertEqual(tid, test_team_second.tid)

        self.assertIsNotNone(models.Team.query.get(test_team_first.tid))
        self.restoreState()

    @base.authenticated_test
    def testCantSwitchAfterStart(self):
        self.patchState('DURING')
        test_team = self.createTeam('test')
        resp = self.changeTeam(test_team.tid, test_team.code)
        self.assert403(resp)
        self.restoreState()


class AttachmentTest(base.RestTestCase):

    PATH = '/api/attachments/%s'
    ATTACHMENT_FIELDS = ('aid', 'filename', 'challenges')

    text = "This is a test"
    name = "test.txt"

    def uploadFile(self, filename, text):
        with self.admin_client as c:
            string = StringIO.StringIO()
            string.write(text)
            string.seek(0)
            return c.post('/api/attachments', data={
                'file': (string, filename)
            })

    def fetchFile(self, aid):
        with self.admin_client as c:
            return c.get(self.PATH % aid)

    def testUploadFile(self):
        resp = self.uploadFile("test.txt", "This is a test")
        self.assert200(resp)
        # Calculated using an external sha256 tool
        self.assertEquals(
                resp.json['aid'],
                "c7be1ed902fb8dd4d48997c6452f5d7e"
                "509fbcdbe2808b16bcf4edce4c07d14e")

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
            getresp = c.get('/attachments/%s' % postresp.json['aid'])
            self.assert200(getresp)

    def testFileRetrievalValue(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            getresp = c.get('/attachment/%s' % postresp.json['aid'])
            self.assertEqual(getresp.get_data(), self.text)

    def testFileDelete(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            delresp = c.delete('/api/attachments/%s' % postresp.json['aid'])
            self.assert200(delresp)

    def testDeletionRemovesFile(self):
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            c.delete('/api/attachments/%s' % postresp.json['aid'])
        with self.admin_client as c:
            getresp = c.get('/api/attachments/%s' % postresp.json['aid'])
            self.assert404(getresp)

    def testFileUpdate(self):
        new_name = "file.png"
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            putresp = c.put(
                    '/api/attachments/%s' % postresp.json['aid'],
                    data=json.dumps({
                        'filename': new_name,
                        'aid': postresp.json['aid'],
                        'challenges': [],
                        }), content_type="application/json")
            self.assert200(putresp)

    def testUpdateChangesName(self):
        new_name = "file.png"
        postresp = self.uploadFile(self.name, self.text)
        with self.admin_client as c:
            c.put('/api/attachments/%s' % postresp.json['aid'],
                  data=json.dumps({
                        'filename': new_name,
                        'aid': postresp.json['aid'],
                        'challenges': [],
                        }), content_type="application/json")
            getresp = c.get('/api/attachments/%s' % postresp.json['aid'])
            self.assertEqual(getresp.json['filename'], new_name)


class UserTest(base.RestTestCase):

    PATH = '/api/users/%d'
    USER_FIELDS = ('admin', 'nick', 'email', 'team_tid', 'uid')

    def testGetAnonymous(self):
        path = self.PATH % makeTestUser().uid
        with self.queryLimit(0):
            self.assert403(self.client.get(path))

    def testGetNonExistent(self):
        path = self.PATH % 999
        with self.queryLimit(0):
            resp = self.client.get(path)
        self.assert403(resp)

    testGetNonExistentAuth = base.authenticated_test(
            testGetNonExistent)

    @base.admin_test
    def testGetNonExistentAdmin(self):
        path = self.PATH % 999
        with self.queryLimit(1):
            resp = self.client.get(path)
        self.assert404(resp)

    @base.authenticated_test
    def testGetSelf(self):
        user = self.authenticated_client.user
        with self.queryLimit(1):
            resp = self.client.get(self.PATH % user.uid)
        self.assert200(resp)
        self.assertEqual(user.email, resp.json['email'])
        self.assertEqual(user.nick, resp.json['nick'])
        self.assertEqual(user.admin, resp.json['admin'])

    @base.authenticated_test
    def testUpdateUser(self):
        user = self.authenticated_client.user
        data = {'password': 'hunter3'}  # for security
        with self.queryLimit(2):
            self.assert200(self.putJSON(
                self.PATH % user.uid,
                data))

    @base.authenticated_test
    def testUpdateUserNoAccess(self):
        uid = self.admin_client.user.uid
        data = {'password': 'hunter3'}
        with self.queryLimit(0):
            resp = self.putJSON(self.PATH % uid, data)
            self.assert403(resp)

    @base.admin_test
    def testUpdateUserAdmin(self):
        uid = self.authenticated_client.user.uid
        data = {'nick': 'Lame'}
        with self.queryLimit(2):
            resp = self.putJSON(self.PATH % uid, data)
        self.assert200(resp)
        self.assertEqual('Lame', resp.json['nick'])
        self.assertNotEqual(
                'Lame',
                self.authenticated_client.user.team.name)

    @base.admin_test
    def testUpdateUsersNoTeams(self):
        uid = self.authenticated_client.user.uid
        self.app.config['TEAMS'] = False
        data = {'nick': 'Lame'}
        with self.queryLimit(3):
            resp = self.putJSON(self.PATH % uid, data)
        self.assert200(resp)
        self.assertEqual('Lame', resp.json['nick'])
        self.assertEqual('Lame', self.authenticated_client.user.team.name)

    @base.admin_test
    def testUpdateUserPromote(self):
        user = self.authenticated_client.user
        data = {'nick': user.nick, 'admin': True}
        # yes, this is a lot, but promoting is infrequent
        with self.queryLimit(7):
            resp = self.putJSON(self.PATH % user.uid, data)
        self.assert200(resp)
        self.assertTrue(resp.json['admin'])

    @base.admin_test
    def testUpdateUserDemote(self):
        user = self.admin_client.user
        data = {'nick': user.nick, 'admin': False}
        with self.queryLimit(3):
            resp = self.putJSON(self.PATH % user.uid, data)
        self.assert200(resp)
        self.assertFalse(resp.json['admin'])

    @base.authenticated_test
    def testUpdateUserNoSelfPromotion(self):
        uid = self.authenticated_client.user.uid
        data = {'admin': True}
        with self.queryLimit(1):
            resp = self.putJSON(self.PATH % uid, data)
        self.assert200(resp)
        self.assertFalse(resp.json['admin'])

    @base.admin_test
    def testUpdateUserNoAnswers(self):
        user = self.authenticated_client.user
        team = self.authenticated_client.user.team
        chall = models.Challenge.create('Foo', 'Foo', 1, 'Foo', 'foo')
        models.Answer.create(chall, team, 'Foo')
        models.db.session.commit()
        data = {'nick': user.nick, 'admin': True}
        with self.queryLimit(3):
            resp = self.putJSON(self.PATH % user.uid, data)
        self.assert400(resp)
        user = models.User.query.get(user.uid)
        self.assertFalse(user.admin)

    @base.authenticated_test
    def testGetUsersNoAccess(self):
        with self.queryLimit(0):
            resp = self.client.get('/api/users')
        self.assert403(resp)

    @base.admin_test
    def testGetUsers(self):
        self.admin_client.user
        with self.queryLimit(1):
            resp = self.client.get('/api/users')
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
        # TODO: maybe optimize?
        with self.client:
            with self.queryLimit(9):
                resp = self.postJSON('/api/users', data)
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
        with self.client:
            with self.queryLimit(8):
                resp = self.postJSON('/api/users', data)
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
        with self.client:
            with self.queryLimit(1):
                resp = self.postJSON('/api/users', data)
            self.assert400(resp)

    @base.authenticated_test
    def testRegisterUserLoggedInFails(self):
        data = self.default_data()
        with self.queryLimit(0):
            resp = self.postJSON('/api/users', data)
        self.assert400(resp)

    def testRegisterUserNoNick(self):
        data = self.default_data()
        del data['nick']
        with self.queryLimit(0):
            self.assert400(self.postJSON('/api/users', data))

    def testRegisterUserNoTeam(self):
        data = self.default_data()
        del data['team_name']
        del data['team_id']
        with self.queryLimit(0):
            self.assert400(self.postJSON('/api/users', data))


class TeamTest(base.RestTestCase):

    LIST_URL = '/api/teams'

    def setUp(self):
        super(TeamTest, self).setUp()
        self.user = makeTestUser()
        self.team = makeTestTeam(self.user)
        self.team_path = '/api/teams/%d' % self.team.tid

    @base.authenticated_test
    def testGetTeam(self):
        with self.queryLimit(4):
            resp = self.client.get(self.team_path)
        self.assert200(resp)
        self.assertEqual(0, len(resp.json['players']))
        self.assertEqual(self.team.name, resp.json['name'])
        # TODO: check other fields

    def testGetTeamAnonymous(self):
        with self.queryLimit(0):
            self.assert403(self.client.get(self.team_path))

    @base.admin_test
    def testGetTeamAdmin(self):
        with self.queryLimit(4):
            resp = self.client.get(self.team_path)
        self.assert200(resp)
        self.assertEqual(1, len(resp.json['players']))

    @base.admin_test
    def testUpdateTeamAdmin(self):
        data = {'name': 'Updated'}
        with self.queryLimit(6):
            resp = self.putJSON(self.team_path, data)
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


class SessionTest(base.RestTestCase):

    PATH = '/api/session'

    def testGetSessionAnonymous(self):
        self.assert403(self.client.get(self.PATH))

    @base.authenticated_test
    def testGetSessionAuthenticated(self):
        with self.queryLimit(1):
            resp = self.client.get(self.PATH)
        self.assert200(resp)
        self.assertEqual(
                self.authenticated_client.user.nick,
                resp.json['user']['nick'])
        self.assertEqual(
                self.authenticated_client.team.name,
                resp.json['team']['name'])

    @base.admin_test
    def testGetSessionAdmin(self):
        with self.queryLimit(1):
            resp = self.client.get(self.PATH)
        self.assert200(resp)
        self.assertEqual(
                self.admin_client.user.nick,
                resp.json['user']['nick'])
        self.assertTrue(resp.json['user']['admin'])
        self.assertItemsEqual(
                {'tid': 0, 'score': 0, 'name': None,
                    'code': None},
                resp.json['team'])

    def testSessionLoginSucceeds(self):
        data = {
            'email': self.authenticated_client.user.email,
            'password': self.authenticated_client.password,
        }
        with self.client:
            with self.queryLimit(4):
                resp = self.postJSON(self.PATH, data)
            self.assert200(resp)
            self.assertEqual(
                    flask.session['user'],
                    self.authenticated_client.user.uid)
            self.assertEqual(
                    flask.session['team'],
                    self.authenticated_client.team.tid)
            self.assertFalse(flask.session['admin'])
            self.assertEqual(
                    flask.g.user.email,
                    self.authenticated_client.user.email)

    def testSessionLoginFailsBadPassword(self):
        data = {
            'email': self.authenticated_client.user.email,
            'password': 'wrong',
        }
        with self.client:
            with self.queryLimit(1):
                resp = self.postJSON(self.PATH, data)
            self.assert403(resp)
            self.assertIsNone(flask.session.get('user'))
            self.assertIsNone(flask.session.get('team'))
            self.assertIsNone(flask.session.get('admin'))

    def testSessionLoginFailsBadUser(self):
        data = {
            'email': 'no@example.com',
            'password': 'wrong',
        }
        with self.client:
            with self.queryLimit(1):
                resp = self.postJSON(self.PATH, data)
            self.assert403(resp)
            self.assertIsNone(flask.session.get('user'))
            self.assertIsNone(flask.session.get('team'))
            self.assertIsNone(flask.session.get('admin'))

    @base.admin_test
    def testSessionLoginAlreadyLoggedIn(self):
        data = {
            'email': self.authenticated_client.user.email,
            'password': self.authenticated_client.password,
        }
        # This makes sure admin->non-admin downgrades properly
        with self.client:
            with self.queryLimit(4):
                resp = self.postJSON(self.PATH, data)
            self.assert200(resp)
            self.assertEqual(
                    flask.session['user'],
                    self.authenticated_client.user.uid)
            self.assertEqual(
                    flask.session['team'],
                    self.authenticated_client.team.tid)
            self.assertFalse(flask.session['admin'])
            self.assertEqual(
                    flask.g.user.email,
                    self.authenticated_client.user.email)

    @base.authenticated_test
    def testSessionLogout(self):
        with self.client as c:
            with self.queryLimit(1):
                resp = c.delete(self.PATH)
            self.assert200(resp)
            self.assertIsNone(flask.session.get('user'))
            self.assertIsNone(flask.session.get('team'))
            self.assertIsNone(flask.session.get('admin'))

    def testSessionLogoutAnonymous(self):
        with self.client as c:
            with self.queryLimit(0):
                resp = c.delete(self.PATH)
            self.assert200(resp)
            self.assertIsNone(flask.session.get('user'))
            self.assertIsNone(flask.session.get('team'))
            self.assertIsNone(flask.session.get('admin'))


class ChallengeTest(base.RestTestCase):

    PATH_LIST = '/api/challenges'
    PATH_SINGLE = '/api/challenges/%d'

    def setUp(self):
        super(ChallengeTest, self).setUp()
        self.challs, _ = makeTestChallenges()
        self.chall = self.challs[0]
        self.PATH_SINGLE %= self.chall.cid

    def testGetListAnonymous(self):
        with self.queryLimit(0):
            self.assert403(self.client.get(self.PATH_LIST))

    testGetListAuthenticated = base.authenticated_test(
            testGetListAnonymous)

    @base.admin_test
    def testGetListAdmin(self):
        # TODO: fix to not be O(n)
        with self.queryLimit(None):
            resp = self.client.get(self.PATH_LIST)
        self.assert200(resp)
        self.assertEqual(len(self.challs), len(resp.json['challenges']))

    def newChallengeData(self):
        return {
            'name': 'Chall 1',
            'description': 'Challenge 1',
            'points': 200,
            'answer': 'abc',
            'cat_slug': self.chall.cat_slug,
            'unlocked': True
        }

    def testCreateChallengeAnonymous(self):
        data = self.newChallengeData()
        with self.queryLimit(0):
            self.assert403(self.postJSON(
                self.PATH_LIST, data))

    testCreateChallengeAuthenticated = base.authenticated_test(
            testCreateChallengeAnonymous)

    @base.admin_test
    def testCreateChallenge(self):
        # TODO: variants
        data = self.newChallengeData()
        # TODO: optimize count
        with self.queryLimit(8):
            resp = self.postJSON(self.PATH_LIST, data)
        self.assert200(resp)
        for field in ('name', 'description', 'points', 'unlocked'):
            self.assertEqual(data[field], resp.json[field])

    def getUpdateData(self):
        return {
            'name': 'Renamed',
            'points': 1,
            'weight': 12,
            'unlocked': False
            }

    @base.admin_test
    def testUpdateChallenge(self):
        data = self.getUpdateData()
        with self.queryLimit(6):
            resp = self.putJSON(self.PATH_SINGLE, data)
        self.assert200(resp)
        for k in data.keys():
            self.assertEqual(data[k], resp.json[k])

    def testUpdateChallengeAnonymous(self):
        data = self.getUpdateData()
        with self.queryLimit(0):
            self.assert403(self.putJSON(self.PATH_SINGLE, data))

    testUpdateChallengeAuthenticated = base.authenticated_test(
            testUpdateChallengeAnonymous)

    @base.admin_test
    def testGetSingleton(self):
        with self.queryLimit(6):
            resp = self.client.get(self.PATH_SINGLE)
        self.assert200(resp)
        for field in ('name', 'points', 'description', 'unlocked'):
            self.assertEqual(getattr(self.chall, field), resp.json[field])

    def testGetSingletonAnonymous(self):
        with self.queryLimit(0):
            self.assert403(self.client.get(self.PATH_SINGLE))

    testGetSingletonAuthenticated = base.authenticated_test(
            testGetSingletonAnonymous)

    @base.admin_test
    def testDeleteChallenge(self):
        with self.queryLimit(5):
            self.assert200(self.client.delete(self.PATH_SINGLE))

    def testDeleteChallengeAnonymous(self):
        with self.queryLimit(0):
            self.assert403(self.client.delete(self.PATH_SINGLE))

    testDeleteChallengeAuthenticated = base.authenticated_test(
            testDeleteChallengeAnonymous)


class ScoreboardTest(base.RestTestCase):

    PATH = '/api/scoreboard'

    def setUp(self):
        super(ScoreboardTest, self).setUp()
        data.create_all()  # Make a bunch of data for scoreboard

    def testGetScoreboard(self):
        resp = self.client.get(self.PATH)
        self.assert200(resp)
        # TODO: check contents


class CategoryTest(base.RestTestCase):

    PATH_LIST = '/api/categories'
    PATH_SINGLE = '/api/categories/%s'

    def setUp(self):
        super(CategoryTest, self).setUp()
        self.challs, self.cats = makeTestChallenges()
        self.cat = self.cats[0]
        self.PATH_SINGLE %= self.cat.slug

    def _testGetList(self):
        with self.queryLimit(3):
            resp = self.client.get(self.PATH_LIST)
        self.assert200(resp)
        self.assertEqual(len(self.cats), len(resp.json['categories']))
        # TODO: check that the expected fields are visible and that others are
        # not.

    testGetListAuthenticated = base.authenticated_test(_testGetList)
    testGetListAdmin = base.admin_test(_testGetList)

    def testGetListAnonymous(self):
        with self.queryLimit(0):
            resp = self.client.get(self.PATH_LIST)
        self.assert403(resp)

    def testCreateCategoryFails(self):
        data = {
            'name': 'New',
            'description': 'New Category',
        }
        with self.queryLimit(0):
            resp = self.postJSON(self.PATH_LIST, data)
        self.assert403(resp)
        self.assertEqual(len(self.cats), models.Category.query.count())

    testCreateCategoryFailsAuthenticated = base.authenticated_test(
            testCreateCategoryFails)

    @base.admin_test
    def testCreateCategory(self):
        data = {
            'name': 'New',
            'description': 'New Category',
        }
        with self.queryLimit(6):
            resp = self.postJSON(self.PATH_LIST, data)
        self.assert200(resp)
        for f in ('name', 'description'):
            self.assertEqual(data[f], resp.json[f])
        cat = models.Category.query.get(resp.json['slug'])
        for f in ('name', 'description'):
            self.assertEqual(data[f], getattr(cat, f))

    def testDeleteCategoryFails(self):
        with self.queryLimit(0):
            resp = self.client.delete(self.PATH_SINGLE)
        self.assert403(resp)
        self.assertIsNotNone(models.Category.query.get(self.cat.slug))

    testDeleteCategoryFailsAuthenticated = base.authenticated_test(
            testDeleteCategoryFails)

    @base.admin_test
    def testDeleteNonEmptyCategory(self):
        with self.queryLimit(3):
            resp = self.client.delete(self.PATH_SINGLE)
        self.assert400(resp)
        self.assertIsNotNone(models.Category.query.get(self.cat.slug))

    @base.admin_test
    def testDeleteEmptyCategory(self):
        for i in self.cat.challenges:
            models.db.session.delete(i)
        models.db.session.commit()
        with self.queryLimit(3):
            resp = self.client.delete(self.PATH_SINGLE)
        self.assert200(resp)
        self.assertIsNone(models.Category.query.get(self.cat.slug))

    def testGetCategoryAnonymous(self):
        with self.queryLimit(0):
            self.assert403(self.client.get(self.PATH_SINGLE))

    def _testGetCategory(self):
        with self.queryLimit(None):
            resp = self.client.get(self.PATH_SINGLE)
        self.assert200(resp)

    testGetCategoryAuthenticated = base.authenticated_test(
            _testGetCategory)
    testGetCategoryAdmin = base.admin_test(_testGetCategory)

    def testUpdateCategoryAnonymous(self):
        with self.queryLimit(0):
            resp = self.putJSON(self.PATH_SINGLE, {
                'name': 'new name'})
        self.assert403(resp)

    testUpdateCategoryAuthenticated = base.authenticated_test(
            testUpdateCategoryAnonymous)

    @base.admin_test
    def testUpdateCategoryAdmin(self):
        data = {'name': 'new name'}
        with self.queryLimit(None):
            resp = self.putJSON(self.PATH_SINGLE, data)
        self.assert200(resp)
        self.assertEqual(data['name'], resp.json['name'])
        cat = models.Category.query.get(self.cat.slug)
        self.assertEqual(data['name'], cat.name)


class AnswerTest(base.RestTestCase):

    PATH = '/api/answers'

    def setUp(self):
        super(AnswerTest, self).setUp()
        cat = models.Category.create('test', 'test')
        self.answer = 'foobar'
        self.points = 100
        self.chall = models.Challenge.create(
                'test', 'test', self.points,
                self.answer, cat.slug, unlocked=True)
        self.cid = self.chall.cid
        models.db.session.commit()

    def testSubmitAnonymous(self):
        with self.queryLimit(0):
            self.assert403(self.postJSON(self.PATH, {
                'cid': self.cid,
                'answer': self.answer,
            }))

    @base.admin_test
    def testSubmitAdmin_Regular(self):
        with self.queryLimit(0):
            self.assert400(self.postJSON(self.PATH, {
                'cid': self.cid,
                'answer': self.answer,
            }))

    @base.admin_test
    def testSubmitAdmin_Override(self):
        team = models.Team.create('crash_override')
        models.db.session.commit()
        with self.queryLimit(7):
            resp = self.postJSON(self.PATH, {
                'cid': self.cid,
                'tid': team.tid,
            })
        self.assert200(resp)
        self.assertEqual(self.points, resp.json['points'])

    @base.authenticated_test
    def testSubmitCorrect(self):
        with self.queryLimit(6):
            resp = self.postJSON(self.PATH, {
                'cid': self.cid,
                'answer': self.answer,
            })
        self.assert200(resp)
        print resp.json
        self.assertEqual(self.points, resp.json['points'])

    @base.authenticated_test
    def testSubmitIncorrect(self):
        old_score = self.client.team.score
        with self.queryLimit(2):
            resp = self.postJSON(self.PATH, {
                'cid': self.cid,
                'answer': 'incorrect',
            })
        self.assert403(resp)
        team = models.Team.query.get(self.client.team.tid)
        self.assertEqual(old_score, team.score)

    @base.authenticated_test
    def testSubmitDouble(self):
        models.Answer.create(self.chall, self.client.team, '')
        old_score = self.client.team.score
        with self.queryLimit(4):
            resp = self.postJSON(self.PATH, {
                'cid': self.cid,
                'answer': self.answer,
            })
        self.assert403(resp)
        team = models.Team.query.get(self.client.team.tid)
        self.assertEqual(old_score, team.score)


class ConfigTest(base.RestTestCase):

    PATH = '/api/config'

    def makeTestGetConfig(extra_keys=None):
        extra_keys = set(extra_keys or [])

        def testGetConfig(self):
            with self.queryLimit(0):
                resp = self.client.get(self.PATH)
            self.assert200(resp)
            expected_keys = set((
                    'teams',
                    'sbname',
                    'news_mechanism',
                    'news_poll_interval',
                    'csrf_token',
                    'rules',
                    'game_start',
                    'game_end',
                    'login_url',
                    'register_url',
                    'login_method',
                    'scoring',
            ))
            expected_keys |= extra_keys
            self.assertEqual(expected_keys, set(resp.json.keys()))
        return testGetConfig

    testGetConfig = makeTestGetConfig()
    testGetConfigAuthenticated = base.authenticated_test(
            makeTestGetConfig())
    testGetConfigAdmin = base.admin_test(
            makeTestGetConfig(['validators']))


class NewsTest(base.RestTestCase):

    PATH = '/api/news'

    def setUp(self):
        super(NewsTest, self).setUp()
        models.News.broadcast('test', 'Test message.')
        models.News.unicast(
                self.authenticated_client.team.tid,
                'test', 'Test team message.')
        models.commit()

    def testGetNews(self):
        with self.queryLimit(2):
            resp = self.client.get(self.PATH)
        self.assert200(resp)
        self.assertEqual(1, len(resp.json))

    testGetNewsAdmin = base.admin_test(testGetNews)

    @base.authenticated_test
    def testGetNewsAuthenticated(self):
        with self.queryLimit(2):
            resp = self.client.get(self.PATH)
        self.assert200(resp)
        self.assertEqual(2, len(resp.json))

    def testCreateNews(self):
        with self.queryLimit(0):
            resp = self.postJSON(self.PATH, {
                'message': 'some message',
            })
        self.assert403(resp)

    testCreateNewsAuthenticated = base.authenticated_test(testCreateNews)

    @base.admin_test
    def testCreateNewsAdmin(self):
        msg = 'some message'
        with self.queryLimit(3):
            resp = self.postJSON(self.PATH, {
                'message': msg,
            })
        self.assert200(resp)
        self.assertEqual(self.client.user.nick, resp.json['author'])
        self.assertEqual(msg, resp.json['message'])

    @base.admin_test
    def testCreateTeamNewsAdmin(self):
        msg = 'some message'
        tid = self.authenticated_client.team.tid
        with self.queryLimit(3):
            resp = self.postJSON(self.PATH, {
                'message': msg,
                'tid': tid,
            })
        self.assert200(resp)
        self.assertEqual(self.client.user.nick, resp.json['author'])
        self.assertEqual(msg, resp.json['message'])
        self.assertEqual('Unicast', resp.json['news_type'])
        news = models.News.query.get(resp.json['nid'])
        self.assertEqual(tid, news.audience_team_tid)


class CTFTimeTest(base.RestTestCase):

    PATH = '/api/ctftime/scoreboard'

    def testGetScoreboard(self):
        with self.queryLimit(1):
            resp = self.client.get(self.PATH)
        self.assert200(resp)
        self.assertIn('standings', resp.json)
        standings = resp.json['standings']
        required = set(('pos', 'team', 'score'))
        for i in standings:
            self.assertEqual(required, required & set(i.keys()))
