/**
 * Copyright 2016 Google LLC. All Rights Reserved.
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

var adminNewsCtrls = angular.module('adminNewsCtrls', [
    'globalServices',
    'sessionServices',
    'teamServices',
    ]);

adminNewsCtrls.controller('AdminNewsCtrl', [
    '$scope',
    'errorService',
    'newsService',
    'sessionService',
    'teamService',
    'loadingService',
    function($scope, errorService, newsService, sessionService, teamService,
        loadingService) {
        if (!sessionService.requireAdmin()) return;

        var makeNewsItem = function() {
            return {
                'news_type': 'Broadcast'
            }
        };
        $scope.newsItem = makeNewsItem();
        $scope.teams = teamService.get();
        $scope.submitNews = function() {
            errorService.clearErrors();
            newsService.save($scope.newsItem,
                function() {
                    $scope.newsItem = makeNewsItem();
                    newsService.poll();
                    errorService.success('News item saved.');
                },
                function(msg) {
                    errorService.error(msg);
                });
        };
        loadingService.stop();
    }]);
