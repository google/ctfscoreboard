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

var challengeCtrls = angular.module('challengeCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    ]);

challengeCtrls.controller('ChallengeGridCtrl', [
    '$rootScope',
    '$scope',
    '$location',
    'challengeService',
    'configService',
    'loadingService',
    'scoreService',
    'tagService',
    function($rootScope, $scope, $location, challengeService, configService,
      loadingService, scoreService, tagService) {
      $scope.currChall = null;
      $scope.shownTags = {};
      $scope.config = configService.get();
      $scope.challenges = [];

      var compareChallenges = function(a, b) {
        return (a.weight - b.weight);
      };

      var refresh = function(cb) {
          console.log('Refresh grid.');
          challengeService.get(function(data) {
              data.challenges.sort(compareChallenges);
              $scope.challenges = data.challenges;
              if (cb !== undefined && cb !== null) {
                  cb();
              }
          });
      };

      tagService.getList(function(tags) {
        $scope.allTags = tags.tags;
        for (var i = 0; i < $scope.allTags.length; i++) {
          $scope.shownTags[$scope.allTags[i].tagslug] = 1;
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
        var containsTag = function(chall, tagslug) {
            for (var i = 0; i < chall.tags.length; i++) {
              if (chall.tags[i].tagslug == tagslug) return true;
            }
            return false;
        }

        //Check for prohibition
        for (var i = 0; i < chall.tags.length; i++) {
          var type = $scope.shownTags[chall.tags[i].tagslug];
          if (type == 0) {
            return false;
          }
        }

        //Check for inclusion
        for (var i in $scope.shownTags) {
          if ($scope.shownTags[i] == 2 && !containsTag(chall, i)) {
            return false;
          }
        }
        return true;
      }

      $scope.toggleTag = function(t, click) {
        var tindex = $scope.shownTags[t];
        //Return next permutation
        if (click == 0) {
          tindex += 1;
        } else {
          tindex += 3-1;
        }
        $scope.shownTags[t] = tindex % 3;
      }

      $scope.getSentiment = function(tag) {
        var sentiments = [
          'sentiment_dissatisfied',
          'sentiment_neutral',
          'sentiment_satisfied'];
        return sentiments[$scope.shownTags[tag.tagslug]];
      }

      refresh(loadingService.stop);

      $rootScope.$on('correctAnswer', refresh);
  }]);
