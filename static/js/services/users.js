/**
 * Copyright 2016 Google Inc. All Rights Reserved.
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

var userServices = angular.module('userServices', ['ngResource']);

userServices.service('userService', [
    '$resource',
    function($resource) {
      return $resource('/api/users/:uid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'}
      });
    }]);

userServices.service('passwordResetService', [
    '$resource',
    function($resource) {
        return $resource('/api/pwreset/:email');
    }]);

userServices.service('apiKeyService', [
    '$resource',
    function($resource) {
        return $resource('/api/apikey/:keyid', {}, {
            'create': {method: 'POST'},
            'deleteAll': {method: 'DELETE', params:{}}
        });
    }]);
