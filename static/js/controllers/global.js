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

var globalCtrls = angular.module('globalCtrls', [
    'globalServices',
    'sessionServices',
    ]);

globalCtrls.controller('GlobalCtrl', [
    '$scope',
    'configService',
    function($scope, configService) {
        $scope.config = configService.get();
    }]);

globalCtrls.controller('LoggedInCtrl', [
    '$scope',
    'sessionService',
    function($scope, sessionService) {
      $scope.session = sessionService.session;
      $scope.loggedIn = function(){
        return !!sessionService.session.user;
      };
      $scope.isAdmin = function(){
        return (!!sessionService.session.user &&
          sessionService.session.user.admin);
      };
    }]);

globalCtrls.controller('ErrorCtrl', [
    '$scope',
    'errorService',
    function($scope, errorService) {
      $scope.errors = errorService.errors;

      $scope.$on('$locationChangeStart', function(ev) {
        errorService.clearErrors();
      });
    }]);

globalCtrls.controller('NewsCtrl', [
    '$scope',
    'newsService',
    function($scope, newsService) {
        $scope.latest = 0;
        var updateNews = function(newsItems) {
            var latest = 0;
            angular.forEach(newsItems, function(item) {
                var d = Date.parse(item.timestamp);
                if (d > latest)
                  latest = d;
            });
            if (latest > $scope.latest) {
                // TODO: call attention to new news
                $scope.latest = latest;
                $scope.newsItems = newsItems;
            }
        };

        newsService.registerClient(updateNews);
        newsService.start();
    }]);
