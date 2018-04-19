/**
 * Copyright 2018 Google Inc. All Rights Reserved.
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

var adminTeamCtrls = angular.module('adminTeamCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServices',
    'teamServices',
    'userServices'
    ]);

adminTeamCtrls.controller('AdminTeamsCtrl', [
    '$scope',
    '$routeParams',
    'answerService',
    'challengeService',
    'errorService',
    'sessionService',
    'teamService',
    'loadingService',
    function($scope, $routeParams, answerService, challengeService, errorService,
        sessionService, teamService, loadingService) {
      if (!sessionService.requireAdmin()) return;

      $scope.teams = [];
      $scope.team = null;
      $scope.unsolved = [];
      $scope.grantee = null;

      $scope.updateTeamModal = function() {
        $("#team-rename").modal("show");
      };

      $scope.updateTeam = function() {
        errorService.clearErrors();
        $scope.team.$save({tid: $scope.team.tid},
          function(data) {
            $scope.team = data;
            errorService.error('Saved.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.grantFlag = function(chall) {
        $scope.grantee = chall;
        $("#team-grant").modal("show");
      };

      $scope.grantFlagConfirm = function() {
        answerService.create(
          { cid: $scope.grantee.cid,
            tid: $scope.team.tid },
          function() {
            errorService.error('Flag granted.', 'success');
            refreshTeam($scope.team.tid);
          },
          errorService.error);
      };

      var refreshTeam = function(tid) {
        $scope.team = teamService.get({tid: tid},
          teamLoaded,
          function(data) {
            errorService.error(data);
            loadingService.stop();
          });
      };

      var teamLoaded = function() {
        var tagData = {};
        var solved = [];
        angular.forEach($scope.team.solved_challenges, function(chall) {
          solved.push(chall.cid);
          angular.forEach(chall.tags, function(tag) {
            if (!(tag.tagslug in tagData))
              tagData[tag.tagslug] = chall.points;
            else
              tagData[tag.tagslug] += chall.points;
          });
        });
        $scope.tagData = tagData;
        $scope.scoreHistory = {};
        $scope.scoreHistory[$scope.team.name] = $scope.team.score_history;
        $scope.unsolved = [];

        challengeService.get(function(challs) {
          angular.forEach(challs.challenges, function(ch) {
            if (solved.indexOf(ch.cid) < 0) {
              $scope.unsolved.push(ch);
            }
          });
          loadingService.stop();
        });
      };

      sessionService.requireLogin(function() {
        var tid = $routeParams.tid;
        if (tid) {
          refreshTeam(tid);
        } else {
          teamService.get(function(data) {
            $scope.teams = data.teams;
            loadingService.stop();
          });
        }
      });
    }]);

adminTeamCtrls.controller('AdminUsersCtrl', [
    '$scope',
    '$routeParams',
    'configService',
    'errorService',
    'sessionService',
    'teamService',
    'userService',
    'loadingService',
    function($scope, $routeParams, configService, errorService, sessionService,
      teamService, userService, loadingService) {
      if (!sessionService.requireAdmin()) return;

      $scope.users = [];
      $scope.teams = [];
      $scope.user = null;
      $scope.config = configService.get();

      $scope.updateUser = function() {
        errorService.clearErrors();
        $scope.user.$save({uid: $scope.user.uid},
          function(data) {
            $scope.user = data;
            errorService.error('Saved.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      var getTeam = function(tid) {
        var team = null;
        angular.forEach($scope.teams, function(t) {
          if (t.tid == tid) {
            team = t;
          }
        });
        return team;
      };

      sessionService.requireLogin(function() {
        teamService.get(function(data) {
          $scope.teams = data.teams;
          var uid = $routeParams.uid;
          if (uid) {
            $scope.user = userService.get({uid: uid},
              function() {
                loadingService.stop();
                $scope.user.team = getTeam($scope.user.team_tid);
              });
          } else {
            userService.get(function(data) {
              $scope.users = data.users;
              angular.forEach($scope.users, function(u) {
                u.team = getTeam(u.team_tid);
              });
              loadingService.stop();
            });
          }
        });
      });  // end requireLogin block
    }]);
