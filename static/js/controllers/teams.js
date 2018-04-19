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

var teamCtrls = angular.module('teamCtrls', [
    'teamServices',
    'globalServices',
    ]);

teamCtrls.controller('TeamPageCtrl', [
    '$scope',
    '$routeParams',
    'teamService',
    'errorService',
    'loadingService',
    function($scope, $routeParams, teamService, errorService, loadingService) {
      var tid = $routeParams.tid;
      teamService.get({tid: tid},
          function(team) {
            $scope.team = team;
            var tagData = {};
            angular.forEach(team.solved_challenges, function(chall) {
              angular.forEach(chall.tags, function(tag) {
                if (!(tag.tagslug in tagData))
                  tagData[tag.tagslug] = chall.points;
                else
                  tagData[tag.tagslug] += chall.points;
              });
            });
            $scope.tagData = tagData;
            $scope.scoreHistory = {};
            $scope.scoreHistory[team.name] = team.score_history;
            loadingService.stop();
          },
          function(err) {
            errorService.error('Unable to load team info.');
            loadingService.stop();
          });
    }]);
