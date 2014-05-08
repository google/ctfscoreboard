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

var regCtrls = angular.module('regCtrls', [
    'globalServices',
    'sessionServices',
    'teamServices',
    'userServices'
    ]);

regCtrls.controller('LoginCtrl', [
    '$scope',
    '$location',
    'errorService',
    'sessionService',
    function($scope, $location, errorService, sessionService) {
      if ($location.path().indexOf('/logout') == 0) {
        sessionService.logout();
      }
      $scope.email = '';
      $scope.password = '';
      $scope.login = function() {
        errorService.clearErrors();
        sessionService.login($scope.email, $scope.password,
          function() {
            $location.path('/challenges');
          },
          function(errData) {
            errorService.error(errData);
          });
      };
    }]);

regCtrls.controller('RegistrationCtrl', [
    '$scope',
    '$location',
    'configService',
    'errorService',
    'sessionService',
    'teamService',
    'userService',
    function($scope, $location, configService, errorService, sessionService,
        teamService, userService) {
      $scope.config = configService.get();
      $scope.teams = teamService.get(function() {
        $scope.teams = $scope.teams.teams;
      });
      $scope.register = function() {
        errorService.clearErrors();
        userService.create({
          email: $scope.email,
          nick: $scope.nick,
          password: $scope.password,
          team_id: $scope.team,
          team_name: $scope.team_name,
          team_code: $scope.team_code
        }, function(data) {
          sessionService.refresh();
          $location.path('/challenges');
        }, function(errData) {
          // TODO: more verbose
          errorService.error(errData);
        });
      };
    }]);

regCtrls.controller('ProfileCtrl', [
    '$scope',
    'errorService',
    'sessionService',
    'userService',
    function($scope, errorService, sessionService, userService) {
      $scope.user = null;

      sessionService.requireLogin(function() {
        $scope.user = sessionService.user;
      });

      $scope.updateProfile = function() {
        userService.save({uid: $scope.user.uid}, $scope.user,
          function(data) {
            $scope.user = data;
            sessionService.refresh();
          },
          function(data) {
            errorService.error(data);
          });
      };
    }]);
