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

var scoreboardCtrls = angular.module('scoreboardCtrls', [
    'ngResource',
    'globalServices'
    ]);

scoreboardCtrls.controller('ScoreboardCtrl', [
    '$scope',
    '$resource',
    '$interval',
    'configService',
    'errorService',
    'loadingService',
    function($scope, $resource, $interval, configService, errorService,
        loadingService) {
      $scope.config = configService.get();

      var getHistory = function(scoreboard) {
        var histories = {};
        angular.forEach(scoreboard, function(entry) {
          histories[entry.name] = entry.history;
        });
        return histories;
      };
      
      var refresh = function() {
        errorService.clearErrors();
        $resource('/api/scoreboard').get(
            function(data) {
              $scope.scoreboard = data.scoreboard;
              $scope.scoreHistory = getHistory(data.scoreboard);
              /* Fake for testing */
              $scope.scoreHistory = {
                'a': [
                  {time: '2016-01-19T09:00', score: 100},
                  {time: '2016-01-19T09:10', score: 200},
                  {time: '2016-01-19T09:15', score: 400}
                ]
              };
              loadingService.stop();
            },
            function(data) {
              errorService.error(data);
              loadingService.stop();
            });
      };

      refresh();
      var iprom = $interval(refresh, 60000);

      $scope.$on('$destroy', function() {
          $interval.cancel(iprom);
      });
    }]);
