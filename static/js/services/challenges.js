/**
 * Copyright 2018 Google LLC. All Rights Reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var challengeServices = angular.module('challengeServices', [
    'ngResource',
    'globalServices']);

challengeServices.service('challengeService', [
    '$resource',
    '$rootScope',
    '$cacheFactory',
    '$timeout',
    function($resource, $rootScope, $cacheFactory, $timeout) {
      var cache = $cacheFactory('challengeCache');
      var cacheTimeout = 30000;
      var res = $resource('/api/challenges/:cid', {}, {
        'get': {method: 'GET', cache: cache},
        'save': {method: 'PUT'},
        'create': {method: 'POST'},
        'delete': {method: 'DELETE'},
      });
      this.get = res.get;
      this.delete = res.delete;
      this.save = function() {
        cache.removeAll();
        return res.save.apply(res, arguments);
      };
      this.create = function() {
        cache.removeAll();
        return res.create.apply(res, arguments);
      };
      this.flush = cache.removeAll;
      $rootScope.$on('correctAnswer', cache.removeAll);
      return this;
    }]);

challengeServices.service('tagService', [
    '$resource',
    '$rootScope',
    '$cacheFactory',
    '$timeout',
    function($resource, $rootScope, $cacheFactory, $timeout) {
        var tagCache = $cacheFactory('tagCache');

        this.res = $resource('/api/tags/:tagslug', {}, {
            'get': {method: 'GET', tagCache},
            'save': {method: 'PUT'},
            'create': {method: 'POST'},
        })

        this.get = this.res.get;
        this.save = this.res.save;
        this.create = this.res.create;
        this.delete = this.res.delete;

        this.getList = function(callback) {
            if (this.taglist) {
                callback(this.taglist);
                return;
            }
            this.res.get(angular.bind(this, function(data) {
                this.taglist = data;
                $timeout(
                    angular.bind(this, function() {
                        this.taglist = null;
                        tagCache.removeAll();
                    }),
                30000, false);
                callback(data);
            }))
            $rootScope.$on('$locationChangeSuccess', function() {
                this.taglist = null;
                tagCache.removeAll();
            });
        }

    }
])

challengeServices.service('attachService', [
    '$resource',
    '$rootScope',
    '$cacheFactory',
    '$timeout',
    function($resource, $rootScope, $cacheFactory, $timeout) {
        var attachCache = $cacheFactory('attachCache');

        this.res = $resource('/api/attachments/:aid', {}, {
            'get': {method: 'GET', attachCache},
            'save': {method: 'PUT'},
        })

        this.get = this.res.get;
        this.create = this.res.create;
        this.save = this.res.save;
        this.delete = this.res.delete;

        this.getList = function(callback) {
            if (this.attachlist) {
                callback(this.attachlist);
                return;
            }
            this.res.get(angular.bind(this, function(data) {
                this.attachlist = data;
                $timeout(
                    angular.bind(this, function() {
                        this.attachlist = null;
                        attachCache.removeAll();
                    }),
                30000, false);
                callback(data);
            }))
            $rootScope.$on('$locationChangeSuccess', function() {
                this.attachlist = null;
                attachCache.removeAll();
            });
        }

    }
])

challengeServices.service('answerService', [
    '$resource',
    '$rootScope',
    function($resource, $rootScope) {
      this.res = $resource('/api/answers/:aid', {}, {
        'create': {method: 'POST'}
      });
      this.create = function(what, success, failure) {
        this.res.create(what,
            function(resp) {
              success(resp);
              $rootScope.$broadcast('correctAnswer');
            },
            failure);
      };
    }]);

challengeServices.service('validatorService', [
    '$resource',
    '$rootScope',
    function($resource, $rootScope) {
      this.res = $resource('/api/validator', {}, {
        'create': {method: 'POST'}
      });
      this.create = function(what, success, failure) {
        this.res.create(what,
            function(resp) {
              success(resp);
            },
            failure);
      };
    }]);

challengeServices.service('scoreService', [
    'configService',
    function(configService) {
      this.scoring = 'plain';
      configService.get(angular.bind(this, function(cfg) {
        this.scoring = cfg.scoring;
      }));
      this.getCurrentPoints = function(challenge) {
        if (!challenge)
          return 0;
        if (this.scoring === 'plain')
          return challenge.points;
        if (this.scoring === 'progressive')
          return Math.floor(challenge.points / Math.max(challenge.solves, 1));
      };
    }])
