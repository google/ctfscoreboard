/**
 * Copyright 2014 David Tomaschik <david@systemoverlord.com>
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

var challengeServices = angular.module('challengeServices', ['ngResource']);

challengeServices.service('challengeService', ['$resource',
    function($resource) {
      return $resource('/api/challenges/:cid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'},
      });
    }]);

challengeServices.service('categoryService', ['$resource',
    function($resource) {
      this.catlist = null;

      this.res = $resource('/api/categories/:cid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'},
      });

      this.get = this.res.get;
      this.create = this.res.create;
      this.save = this.res.save;
      this.delete = this.res.delete;

      this.getList = function(callback) {
        // TODO: rewrite this to maintain binding in scopes
        if (this.catlist) {
          callback(this.catlist);
          return;
        }
        this.res.get(angular.bind(this, function(data) {
          this.catlist = data;
          setTimeout(
            angular.bind(this, function() { this.catlist = null; }),
            30000);
          callback(data);
        }));
      };

    }]);

challengeServices.service('answerService', ['$resource',
    function($resource) {
      return $resource('/api/answers/:aid', {}, {
        'create': {method: 'POST'}
      });
    }]);
