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

var sbDirectives = angular.module('sbDirectives', [
        'globalServices'
        ]);

sbDirectives.directive('highlightActive', [
    '$location',
    function($location) {
        return {
            restrict: 'A',
            link: function(scope, element, attrs) {
                scope.$watch(function() { return $location.path(); },
                    function() {
                        if (element[0].pathname == $location.path()) {
                            element.addClass('active');
                        } else {
                            element.removeClass('active');
                        }
                    });
            }
        };
    }]);

sbDirectives.directive('countdownTimer', [
    '$interval',
    'gameTimeService',
    function($interval, gameTimeService) {
        return {
            restrict: 'AE',
            scope: true,
            templateUrl: '/partials/components/countdown.html',
            link: function(scope) {
                var iprom = null;
                var splitTime = function(time) {
                    var t = {};
                    t.seconds = time % 60;
                    time = Math.floor(time/60);
                    t.minutes = time % 60;
                    t.hours = Math.floor(time / 60);
                    return t;
                };
                var refresh = function() {
                    var timeleft = gameTimeService.toStart();
                    if (timeleft > 0) {
                        // Not yet started
                        scope.to = "starts";
                        scope.time = splitTime(timeleft);
                        return;
                    }
                    timeleft = gameTimeService.toEnd();
                    if (timeleft > 0) {
                        // During game
                        scope.to = "ends";
                        scope.time = splitTime(timeleft);
                        return;
                    }
                    // Game over or no end
                    if (iprom) {
                        $interval.cancel(iprom);
                        iprom = null;
                    }
                    if (!gameTimeService.end)
                        scope.message = "Game on!";
                    else
                        scope.message = "Game over.";
                };
                gameTimeService.then(function() {
                    if (!gameTimeService.start && !gameTimeService.end)
                        return;
                    scope.display = true;
                    refresh();
                    iprom = $interval(refresh, 1000);
                });
                scope.display = false;
            }
        };
    }]);
