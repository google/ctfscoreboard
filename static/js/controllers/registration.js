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

var regCtrls = angular.module('regCtrls', [
    'globalServices',
    'sessionServices',
    'teamServices',
    'userServices'
    ]);

regCtrls.controller('LoginCtrl', [
    '$scope',
    '$location',
    '$window',
    'configService',
    'errorService',
    'sessionService',
    'passwordResetService',
    'loadingService',
    function($scope, $location, $window, configService, errorService, sessionService,
        passwordResetService, loadingService) {
      if ($location.path().indexOf('/logout') == 0) {
        sessionService.logout(function() {
          $window.location.href = '/';
        });
        return;
      }

      // Check if we should redirect
      configService.get(function(c) {
        if (c.login_method == "local")
          return;
        $window.location.href = c.login_url;
      });

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
            $scope.password = '';
          });
      };

      $scope.pwreset = function() {
        errorService.clearErrors();
        passwordResetService.get({email: $scope.email},
            function(data) {
                errorService.success(data);
            },
            function(data) {
                errorService.error(data);
            });
      };

      loadingService.stop();
    }]);

regCtrls.controller('RegistrationCtrl', [
    '$scope',
    '$location',
    'configService',
    'errorService',
    'sessionService',
    'teamService',
    'userService',
    'loadingService',
    function($scope, $location, configService, errorService, sessionService,
        teamService, userService, loadingService) {
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
      loadingService.stop();
    }]);

regCtrls.controller('ProfileCtrl', [
    '$scope',
    'configService',
    'errorService',
    'sessionService',
    'userService',
    'loadingService',
    'gameTimeService',
    'teamService', 
    function($scope, configService, errorService, sessionService,
        userService, loadingService, gameTimeService, teamService) {
      $scope.user = null;

      $scope.started = gameTimeService.started;
      $scope.changing = false;

      $scope.startJoin = function() {
        $scope.changing = true;
        $scope.team.code = "";
        $("#team").focus();
      }

      $scope.cancel = function() {
        $scope.changing = false;
        $scope.team.name = $scope.team.originalname;
        $scope.team.code = $scope.team.originalcode;
      }

      $scope.$watch('team.name', function() {
        if (!($scope.teams && $scope.team && $scope.team.name)) return;
        for (var i = 0; i < $scope.teams.length; i++) {
          if ($scope.teams[i].name == $scope.team.name) {
            return $scope.team.tid = $scope.teams[i].tid;
          }
        }
        $scope.team.tid = -1;
      })

      sessionService.requireLogin(function() {
        $scope.user = sessionService.session.user;
        configService.get(function(c) {
            if (c.teams) {
                $scope.team = sessionService.session.team;
                $scope.team.originalname = $scope.team.name;
                $scope.team.originalcode = $scope.team.code;
            }
            loadingService.stop();
        });
        teamService.get(function(c) {
          $scope.teams = c.teams;
        })
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

regCtrls.controller('PasswordResetCtrl', [
    '$scope',
    '$routeParams',
    '$location',
    'passwordResetService',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, $routeParams, $location, passwordResetService,
        errorService, sessionService, loadingService) {
        $scope.email = $routeParams.email;
        $scope.pwreset = function() {
            errorService.clearErrors();
            passwordResetService.save({email: $routeParams.email},
                {
                    'token': $routeParams.token,
                    'password': $scope.password,
                    'password2': $scope.password2
                },
                function(data) {
                    errorService.clearAndInhibit();
                    errorService.success(data);
                    sessionService.refresh();
                    $location.path('/');
                },
                function(data) {
                    errorService.error(data);
                    $scope.password = '';
                    $scope.password2 = '';
                });
        };
        loadingService.stop();
    }]);
