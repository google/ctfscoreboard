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

sbDirectives.directive('loadingOverlay', [
    'loadingService',
    function (loadingService) {
        return {
            restrict: 'A',
            link: function(scope, element, attrs) {
                scope.$watch(function() { return loadingService.getState(); },
                    function() {
                        if (loadingService.getState())
                            element.show();
                        else
                            element.hide();
                    });
            }
        };
    }]);


/* Score over time charts based on Chart.Scatter.js
 * chartData should be an object with structure like:
 * {"label": [{time: datestring, score: value}...], ...}
 */
sbDirectives.directive('scoreChart', [
    function() {
      return {
        restrict: 'AE',
        replace: false,
        scope: {
          chartData: '='
        },
        link: function(scope, element, attrs) {
          if (!Chart || Chart === undefined) {
            console.log('Chart.js is not available.');
            element.remove();
            return;
          }
          var colorScheme = [
            '#a6cee3',
            '#1f78b4',
            '#b2df8a',
            '#33a02c',
            '#fb9a99',
            '#e31a1c',
            '#fdbf6f',
            '#ff7f00',
            '#cab2d6',
            '#6a3d9a',
            '#ffff99',
            '#b15928'];
          scope.$watch('chartData', function() {
            if (scope.chartData === undefined)
              return;
            element.empty();

            var legendWidth = Math.min(100, element.width() * 0.2);

            // Create canvas inside our element
            var canvas = document.createElement("canvas");
            canvas.height = element.height();
            // Leave space for legend
            canvas.width = element.width() - legendWidth;
            element.append(canvas);

            // Prepare a legend
            var legend = document.createElement("div");
            element.append(legend);
            legend.style.width = legendWidth;
            $(legend).addClass('sbchart-legend');

            // Transform data
            var datasets = [];
            angular.forEach(scope.chartData, function(series, label) {
              var color = colorScheme[datasets.length % colorScheme.length];
              var set = {
                label: label,
                strokeColor: color,
                data: []
              };
              angular.forEach(series, function(point) {
                set.data.push({x: new Date(point.time), y: point.score});
              });
              set.data.sort(function(a, b) {
                if (a.x < b.x)
                  return -1;
                if (a.x > b.x)
                  return 1;
                return 0;
              });
              datasets.push(set);
            });
            
            var options = {
              pointDot: false,
              scaleType: "date"
            };

            var ctx = canvas.getContext("2d");
            var scatterChart = new Chart(ctx).Step(datasets, options);
            legend.innerHTML = scatterChart.generateLegend();
          });
        }
      }
    }]);
