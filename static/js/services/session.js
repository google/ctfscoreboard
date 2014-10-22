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

var sessionServices = angular.module('sessionServices', [
    'ngResource',
    'globalServices',
    ]);

sessionServices.service('sessionService', [
    '$resource', '$location', '$rootScope', 'errorService',
    function($resource, $location, $rootScope, errorService) {
      this.sessionData = $resource('/api/session');
      this.session = {
        user: null,
        team: null
      };

      this.login = function(email, password, successCallback, errorCallback) {
        this.sessionData.save({email: email, password: password},
          angular.bind(this, function(data) {
            this.session.user = data.user;
            this.session.team = data.team;
            if (successCallback)
              successCallback();
            $rootScope.$broadcast('sessionLogin');
          }), errorCallback || function() {});
      };

      this.logout = function() {
        this.sessionData.remove();
        this.session.user = null;
        this.session.team = null;
        $rootScope.$broadcast('sessionLogout');
      };

      this.refresh = function(successCallback, errorCallback) {
        // Attempt to load
        this.sessionData.get(angular.bind(this, function(data) {
          this.session.user = data.user;
          this.session.team = data.team;
          if (successCallback)
            successCallback();
        }), errorCallback || function() {});
      };

      this.requireLogin = function(callback, no_redirect) {
        /* If the user is logged in, execute the callback.  Otherwise, redirect
         * to the login. */
        if (this.session.user !== null) {
          return callback();
        }
        return this.refresh(callback,
            function() {
              if (no_redirect)
                return;
              errorService.error('You must be logged in.', 'info');
              $location.path('/login');
            });
      };
      this.refresh();
    }]);

function getss(){
  return angular.element(document).injector().get('sessionService');
}
