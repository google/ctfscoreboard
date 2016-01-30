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
            var catData = {};
            angular.forEach(team.solved_challenges, function(chall) {
              if (!(chall.cat_name in catData))
                catData[chall.cat_name] = chall.points;
              else
                catData[chall.cat_name] += chall.points;
            });
            $scope.categoryData = catData;
            $scope.scoreHistory = {};
            $scope.scoreHistory[team.name] = team.score_history;
            console.log($scope.scoreHistory);
            loadingService.stop();
          },
          function(err) {
            errorService.error('Unable to load team info.');
            loadingService.stop();
          });
    }]);
