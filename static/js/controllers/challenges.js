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

var challengeCtrls = angular.module('challengeCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServices',
    ]);

challengeCtrls.controller('CategoryMenuCtrl', [
    '$scope',
    '$interval',
    'categoryService',
    'sessionService',
    function($scope, $interval, categoryService, sessionService) {
        var updateCategories = function() {
            categoryService.getList(function(data) {
                $scope.categories = data.categories;
            });
        };

        var update;
        var startUpdate = function() {
            updateCategories();
            update = $interval(updateCategories, 60*1000);
        };

        sessionService.requireLogin(startUpdate, true);
        $scope.$on('sessionLogin', startUpdate);
        $scope.$on('sessionLogout', function() {
            $scope.categories = [];
            $interval.cancel(update);
        });
        $scope.$on('correctAnswer', updateCategories);
    }]);

challengeCtrls.controller('CategoryCtrl', [
    '$scope',
    '$routeParams',
    'categoryService',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, $routeParams, categoryService, errorService, sessionService,
      loadingService) {
      errorService.clearErrors();

      var refresh = function(cid) {
        categoryService.get({cid: cid},
            function(cat) {
              $scope.category = cat;
              $scope.category.answers = {};
              $scope.challenges = cat.challenges;
              loadingService.stop();
            });
      };

      $scope.filterUnlocked = function(chall) {
        return chall.unlocked == true;
      };

      var slug = $routeParams.slug;
      if (slug) {
        // Load challenges
        sessionService.requireLogin(function() {
          var found = false;
          categoryService.getList(function(data) {
            angular.forEach(data.categories, function(c) {
              if (c.slug == slug){
                $scope.cid = c.cid;
                refresh(c.cid);
                found = true;
              }
            });
            if (!found) {
              errorService.error('Category not found.');
              loadingService.stop();
            }
          });
        });
      } else {
        loadingService.stop();
      }
    }]);


challengeCtrls.controller('ChallengeGridCtrl', [
    '$scope',
    '$location',
    'categoryService',
    'loadingService',
    'sessionService',
    function($scope, $location, categoryService, loadingService, sessionService) {
      $scope.categories = {};
      $scope.currChall = null;
      var refresh = function() {
          categoryService.getList(function(data) {
              $scope.categories = data.categories;
          });
      };

      $scope.goChallenge = function(chall) {
        $scope.currChall = chall;
        $('#challenge-modal').modal('show');
      };

      $scope.flipSide = function(chall) {
        if (chall.answered)
          return "Solved!";
        else
          return chall.points + " points";
      };

      sessionService.requireLogin(function() {
        refresh();
        loadingService.stop();
      });
  }]);
