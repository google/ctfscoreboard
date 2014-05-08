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
    'configService',
    function($scope, $resource, configService) {
      $scope.config = configService.get();
      $resource('/api/scoreboard').get(
        function(data) {
          $scope.scoreboard = data.scoreboard;
        });
    }]);
