# Copyright 2016 Google LLC. All Rights Reserved.
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


import functools
import json
import flask

from cachelib import MemcachedCache, SimpleCache, NullCache


from scoreboard import main

app = main.get_app()


class CacheWrapper(object):

    def __init__(self, app):
        cache_type = app.config.get('CACHE_TYPE')
        if cache_type == 'memcached':
            host = app.config.get('MEMCACHE_HOST')
            self._cache = MemcachedCache([host])
        elif cache_type == 'local':
            self._cache = SimpleCache()
        else:
            self._cache = NullCache()

    def __getattr__(self, name):
        return getattr(self._cache, name)


global_cache = CacheWrapper(app)


def rest_cache(f_or_key):
    """Mark a function for global caching."""
    override_cache_key = None

    def wrap_func(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if override_cache_key:
                cache_key = override_cache_key
            else:
                try:
                    cache_key = '%s/%s' % (
                            f.im_class.__name__, f.__name__)
                except AttributeError:
                    cache_key = f.__name__
            return _rest_cache_caller(f, cache_key, *args, **kwargs)
        return wrapped
    if isinstance(f_or_key, str):
        override_cache_key = f_or_key
        return wrap_func
    return wrap_func(f_or_key)


def rest_cache_path(f):
    """Cache a result based on the path received."""

    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        cache_key = flask.request.path.encode('utf-8')
        return _rest_cache_caller(f, cache_key, *args, **kwargs)
    return wrapped


def rest_team_cache(f_or_key):
    """Mark a function for per-team caching."""
    override_cache_key = None

    def wrap_func(f):
        @functools.wraps(f)
        def wrapped(*args, **kwargs):
            if flask.g.tid:
                if override_cache_key:
                    cache_key = override_cache_key % (flask.g.tid)
                else:
                    try:
                        cache_key = '%s/%s/%s' % (
                                f.im_class.__name__, f.__name__, flask.g.tid)
                    except AttributeError:
                        cache_key = '%s/%s' % (
                                f.__name__, flask.g.tid)
                return _rest_cache_caller(f, cache_key, *args, **kwargs)
            return f(*args, **kwargs)
        return wrapped
    if isinstance(f_or_key, str):
        override_cache_key = f_or_key
        if '%d' not in override_cache_key:
            raise ValueError('No way to override the key per team!')
        return wrap_func
    return wrap_func(f_or_key)


def delete(key):
    """Delete cache entry."""
    global_cache.delete(key)


def clear():
    """Flush global cache."""
    global_cache.clear()


def delete_team(base_key):
    """Delete team-based cache entry."""
    if not flask.g.tid:
        return
    global_cache.delete(base_key % flask.g.tid)


def _rest_cache_caller(f, cache_key, *args, **kwargs):
    value = global_cache.get(cache_key)
    if value:
        try:
            return _rest_add_cache_header(json.loads(value), True)
        except ValueError:
            pass
    value = f(*args, **kwargs)
    try:
        # TODO: only cache on success
        global_cache.set(cache_key, json.dumps(value))
    except TypeError:
        pass
    return _rest_add_cache_header(value)


def _rest_add_cache_header(rv, hit=False):
    # TODO: check status codes?
    headers = {'X-Cache-Hit': str(hit)}
    if isinstance(rv, str):
        return (rv, 200, headers)
    if isinstance(rv, tuple):
        if len(rv) == 1:
            return (rv[0], 200, headers)
        if len(rv) == 2:
            return (rv[0], rv[1], headers)
        if len(rv) == 3:
            if rv[2] is None:
                return (rv[0], rv[1], headers)
            if isinstance(rv[2], dict):
                rv[2].update(headers)
                return rv
    if isinstance(rv, (list, dict)):
        return rv, 200, headers
    # TODO: might need to support Response objects
    return rv
