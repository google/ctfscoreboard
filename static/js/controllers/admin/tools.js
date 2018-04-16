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

var adminToolCtrls = angular.module('adminToolCtrls', [
    'adminServices',
    'sessionServices',
    ]);

adminToolCtrls.controller('AdminToolCtrl', [
    '$scope',
    'adminToolsService',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, adminToolsService, errorService, sessionService, loadingService) {
        if (!sessionService.requireAdmin()) return;

        $scope.recalculateScores = adminToolsService.recalculateScores;
        $scope.resetScores = function() {
          adminToolsService.resetScores(
            errorService.success, errorService.error);
        };
        $scope.resetPlayers = function() {
          adminToolsService.resetPlayers(
            errorService.success, errorService.error);
        };

        loadingService.stop();
    }]);
