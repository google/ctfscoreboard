# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Cache test module."""

import flask
import mock

from scoreboard.tests import base

from scoreboard import cache


class BaseCacheTest(base.BaseTestCase):
    """Test core caching functionality."""

    def setUp(self):
        super(BaseCacheTest, self).setUp()
        cache.global_cache = cache.SimpleCache()

    def makeMockGet(self, cache_type, cache_host=None):
        orig_config = self.app.config

        def mock_get(key):
            if key == 'CACHE_TYPE':
                return cache_type
            elif key == 'MEMCACHE_HOST':
                return cache_host
            return orig_config.get(key)
        return mock_get

    def testBuildCaches(self):
        """Test that we can build the various types of caches."""
        for ctype in ('memcached', 'local'):
            with mock.patch.object(self.app, 'config') as m:
                m.get = self.makeMockGet(ctype, 'localhost')
                c = cache.CacheWrapper(self.app)
                with self.assertRaises(AttributeError):
                    c._non_existent_attribute_really

    def testRestCache_Basic(self):
        m = mock.Mock()
        m.__name__ = 'mockMethod'
        m.return_value = 5
        wrapped = cache.rest_cache(m)
        self.assertEqual(5, wrapped())
        self.assertEqual(5, wrapped())  # called twice for caching
        m.assert_called_once()

    def testRestCache_Override(self):
        m = mock.Mock()
        m.__name__ = 'mockMethod'
        m.return_value = 8
        wrapped = cache.rest_cache('key')(m)
        self.assertEqual(8, wrapped())
        self.assertEqual(8, wrapped())  # called twice for caching
        m2 = mock.Mock()
        m2.__name__ = 'mockMethod2'
        m2.return_value = 42
        wrapped2 = cache.rest_cache('key')(m2)  # same key
        self.assertEqual(8, wrapped2())
        m.assert_called_once()
        m2.assert_not_called()

    def testRestCachePath(self):
        m = mock.Mock()
        m.__name__ = 'mockMethod'
        m.return_value = 1337
        wrapped = cache.rest_cache_path(m)
        with self.app.test_request_context('/foo/bar'):
            self.assertEqual(1337, wrapped())
        m.return_value = 1338
        with self.app.test_request_context('/foo/bar?baz=1'):
            self.assertEqual(1337, wrapped())
        with self.app.test_request_context('/foo/baz'):
            self.assertEqual(1338, wrapped())

    def testRestTeamCache_Basic(self):
        m = mock.Mock()
        m.__name__ = 'mockMethod'
        m.return_value = 5
        wrapped = cache.rest_team_cache(m)
        with mock.patch.object(flask, 'g'):
            flask.g.tid = 111
            self.assertEqual(5, wrapped())
            m.return_value = 555
            self.assertEqual(5, wrapped())  # called twice for caching
            m.assert_called_once()
            flask.g.tid = 123
            self.assertEqual(555, wrapped())  # different team?

    def testRestTeamCache_Override(self):
        m = mock.Mock()
        m.__name__ = 'mockMethod'
        m.return_value = 5
        with self.assertRaises(ValueError):
            cache.rest_team_cache('foo')(m)
        wrapped = cache.rest_team_cache('foo-%d')(m)
        with mock.patch.object(flask, 'g'):
            flask.g.tid = 111
            self.assertEqual(5, wrapped())
            m.return_value = 555
            self.assertEqual(5, wrapped())  # called twice for caching
            m.assert_called_once()
            flask.g.tid = 123
            self.assertEqual(555, wrapped())  # different team?

    def testRestCacheCaller_NonSerializable(self):
        m = mock.Mock()
        m.return_value = mock.Mock()
        m.return_value.foo = 5
        self.assertEqual(5, cache._rest_cache_caller(m, 'foo').foo)
        m.assert_called_once()

    def testRestCacheCaller_NonLoadable(self):
        cache.global_cache.set('foo', '{ not valid json')
        m = mock.Mock()
        m.return_value = 5
        self.assertEqual(5, cache._rest_cache_caller(m, 'foo'))
        self.assertEqual(5, cache._rest_cache_caller(m, 'foo'))
        m.assert_called_once()

    def testRestAddCacheHeader(self):
        foo = 'foo'
        rv = cache._rest_add_cache_header((foo,))
        self.assertEqual(foo, rv[0])
        self.assertEqual(200, rv[1])
        self.assertTrue('X-Cache-Hit' in rv[2])

        rv = cache._rest_add_cache_header((foo, 404))
        self.assertEqual(foo, rv[0])
        self.assertEqual(404, rv[1])
        self.assertTrue('X-Cache-Hit' in rv[2])

        rv = cache._rest_add_cache_header((foo, 404, None))
        self.assertEqual(foo, rv[0])
        self.assertEqual(404, rv[1])
        self.assertTrue('X-Cache-Hit' in rv[2])

        rv = cache._rest_add_cache_header((foo, 404, {foo: foo}))
        self.assertEqual(foo, rv[0])
        self.assertEqual(404, rv[1])
        self.assertTrue('X-Cache-Hit' in rv[2])

        rv = cache._rest_add_cache_header({foo: foo})
        self.assertTrue(foo in rv[0])
        self.assertEqual(200, rv[1])
        self.assertTrue('X-Cache-Hit' in rv[2])

        rv = cache._rest_add_cache_header(foo)
        self.assertEqual(foo, rv[0])
        self.assertEqual(200, rv[1])
        self.assertTrue('X-Cache-Hit' in rv[2])

        # Passthrough cases
        bar = mock.Mock()
        self.assertEqual(bar, cache._rest_add_cache_header(bar))
        baz = (1, 2, 3, 4)
        self.assertEqual(baz, cache._rest_add_cache_header(baz))
        bang = (1, 2, 3)
        self.assertEqual(bang, cache._rest_add_cache_header(bang))
