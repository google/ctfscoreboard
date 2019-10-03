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

var adminPageCtrls = angular.module('adminPageCtrls', [
    'globalServices',
    'sessionServices',
    'pageServices',
    'ngRoute',
    ]);

adminPageCtrls.controller('AdminPageCtrl', [
    '$scope',
    '$routeParams',
    'errorService',
    'pageService',
    'sessionService',
    'loadingService',
    function($scope, $routeParams, errorService, pageService, sessionService,
        loadingService) {
        if (!sessionService.requireAdmin()) return;

        var path = $routeParams.path;

        $scope.action = 'New Page: ' + path;
        
        var goEdit = function() {
            $scope.action = 'Edit Page: ' + path;
        };

        $scope.save = function() {
            errorService.clearErrors();
            pageService.save({path: path}, $scope.page,
                function(data) {
                    $scope.page = data;
                    errorService.success('Saved.');
                    goEdit();
                },
                function(data) {
                    errorService.error(data);
                });
        };

        $scope.page = {path: path};

        pageService.get({path: path},
            function(data) {
                goEdit();
                $scope.page = data;
                loadingService.stop();
            },
            function(data) {
                loadingService.stop();
                if (data.status == 404)
                    // Don't care, creating a new page?
                    return;
                errorService.error(data);
            });
    }]);
