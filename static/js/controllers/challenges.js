/**
 * Copyright 2016 Google Inc. All Rights Reserved.
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
                $scope.slug = c.slug;
                refresh(c.slug);
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
    'scoreService',
    'sessionService',
    'tagService',
    function($scope, $location, categoryService, loadingService, scoreService,
      sessionService, tagService) {
      $scope.categories = {};
      $scope.currChall = null;
      $scope.shownTags = {};
      var refresh = function() {
          categoryService.getList(function(data) {
              $scope.categories = data.categories;
          });
      };

      tagService.getList(function(tags) {
        $scope.allTags = tags.tags
        for (var i = 0; i < $scope.allTags.length; i++) {
          $scope.shownTags[$scope.allTags[i].tagslug] = 2
        }
      })

      $scope.goChallenge = function(chall) {
        $scope.currChall = chall;
        $('#challenge-modal').modal('show');
      };

      $scope.flipSide = function(chall) {
        if (chall.answered)
          return "Solved! (" + scoreService.getCurrentPoints(chall) + " points)";
        else
          return scoreService.getCurrentPoints(chall) + " points";
      };

      $scope.tagsAllowed = function(chall) {
        for (var i = 0; i < chall.tags.length; i++) {
          var type = $scope.shownTags[chall.tags[i].tagslug]
          if (type == 0) {
            return false
          }
        }

        for (var i = 0; i < chall.tags.length; i++) {
          var type = $scope.shownTags[chall.tags[i].tagslug]
          if (type == 2) {
            return true
          }
        }
        return false;
      }

      $scope.toggleTag = function(t, click) {
        var tindex = $scope.shownTags[t]
        //Return next permutation
        if (click == 0) {
          tindex += 1
        } else {
          tindex += 3-1
        }
        $scope.shownTags[t] = tindex % 3
      }

      $scope.getSentiment = function(tag) {
        var sentiments = ['sentiment_dissatisfied', 'sentiment_neutral', 'sentiment_satisfied']
        return sentiments[$scope.shownTags[tag.tagslug]]
      }

      sessionService.requireLogin(function() {
        refresh();
        loadingService.stop();
      });
  }]);
