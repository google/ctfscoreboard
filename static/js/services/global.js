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

/* Global services */
var globalServices = angular.module('globalServices', ['ngResource']);

globalServices.service('configService', ['$resource',
    function($resource) {
      return $resource('/api/config', {}, {
        'get': {cache: true}
      });
    }]);

globalServices.service('errorService',
    function() {
      this.errors = [];
      this.clearErrors = function() {
        this.errors.length = 0;
      };
      this.error = function(msg, severity) {
        severity = severity || 'danger';
        msg = (msg.data && msg.data.message) || msg.message || msg.data || msg;
        this.errors.push({severity: severity, msg: msg});
      };
      this.success = function(msg) {
        this.error(msg, 'success');
      }
    });

