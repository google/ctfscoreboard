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

var sbDirectives = angular.module('sbDirectives', [
        'challengeServices',
        'globalServices',
        'ngSanitize'
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
                            element.addClass('active is-active');
                        } else {
                            element.removeClass('active is-active');
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
    '$filter',
    function($filter) {
      return {
        restrict: 'AE',
        replace: false,
        scope: {
          chartData: '=',
          startDate: '@',
          endDate: '@'
        },
        link: function(scope, element, attrs) {
          if (!Chart || Chart === undefined) {
            console.log('Chart.js is not available.');
            element.remove();
            return;
          }
          var padding = 5;
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
          var withLegend = (attrs.withLegend !== undefined);

          var getDate = function(d) {
            if (d === undefined)
              return null;
            return new Date(d);
          };

          scope.$watch('chartData', function() {
            if (scope.chartData === undefined)
              return;
            element.empty();

            var legendWidth = Math.min(100, Math.floor(element.width() * 0.2));

            var startDate = getDate(scope.startDate);
            var endDate = getDate(scope.endDate);

            // Transform data
            var datasets = [];
            angular.forEach(scope.chartData, function(series, label) {
              var color = colorScheme[datasets.length % colorScheme.length];
              var set = {
                label: $filter('escapeHtml')(label),
                strokeColor: color,
                data: []
              };
              var rawData = [];
              angular.forEach(series, function(point) {
                rawData.push({x: new Date(point.when), y: point.score});
              });
              if (rawData.length == 0)
                return;
              rawData.sort(function(a, b) {
                if (a.x < b.x)
                  return -1;
                if (a.x > b.x)
                  return 1;
                return 0;
              });
              // Trim for start and end date
              if (startDate != null || endDate != null) {
                var startValue = null;
                var endValue = null;
                angular.forEach(rawData, function(point) {
                  if (startDate !== null && point.x < startDate) {
                    startValue = point.y;
                  } else if (endDate !== null && point.x > endDate) {
                    if (endValue !== null) {
                      set.data.push({x: endDate, y: endValue});
                      endValue = null;
                    }
                  } else {
                    if (startValue !== null) {
                      set.data.push({x: startDate, y: startValue});
                      startValue = null;
                    }
                    set.data.push(point);
                  }
                });
              } else {
                set.data = rawData;
              } // end pruning data
              // Nothing after pruning
              if (set.data.length == 0) {
                if (startValue != null) {
                  set.data.push({x: startDate, y: startValue});
                } else {
                  return;
                }
              }
              // Extend to present
              var endPointDate = endDate || (new Date());
              var last = set.data[set.data.length - 1];
              if (last.x < endPointDate)
                set.data.push({x: endPointDate, y: last.score});
              datasets.push(set);
            });

            var options = {
              pointDot: false,
              scaleType: "date",
              useUtc: false,
              scaleTimeFormat: "HH:MM",
              scaleDateTimeFormat: "mmm d, HH:MM"
            };

            // Create canvas inside our element
            var canvas = document.createElement("canvas");
            canvas.height = element.height();
            if (withLegend)
              // Leave space for legend
              canvas.width = element.width() - legendWidth - padding;
            else
              canvas.width = element.width() - padding;
            element.append(canvas);

            var legend;
            if (withLegend) {
              // Prepare a legend
              legend = document.createElement("div");
              element.append(legend);
              legend.style.width = legendWidth;
              legend.style.maxWidth = legendWidth;
              $(legend).addClass('sbchart-legend');
            }

            var ctx = canvas.getContext("2d");
            var stepChart = new Chart(ctx).Step(datasets, options);
            if (withLegend)
              legend.innerHTML = stepChart.generateLegend();
          });
        }
      };
    }]);


/* Draw a donut chart of, well, anything.
 * Expects data like:
 * {category: value}
 */
sbDirectives.directive('donutChart', [
    '$filter',
    function($filter) {
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
          var withLegend = (attrs.withLegend !== undefined);

          scope.$watch('chartData', function() {
            /* TODO: add a legend */
            if (scope.chartData === undefined)
              return;
            element.empty();

            // Massage the data
            var dataset = [];
            var numElements = 0;
            angular.forEach(scope.chartData, function() {
              numElements++;
            });
            var getColors;
            var colorIdx = 0;
            if ((numElements * 2) < colorScheme.length) {
              getColors = function() {
                var rv = [colorScheme[colorIdx * 2], colorScheme[colorIdx * 2 + 1]];
                colorIdx ++;
                return rv;
              };
            } else {
              getColors = function() {
                var rv = [colorScheme[colorIdx], colorScheme[colorIdx]];
                colorIdx ++;
                return rv;
              };
            }
            angular.forEach(scope.chartData, function(value, key) {
              var colors = getColors();
              dataset.push({
                value: value,
                color: colors[0],
                highlight: colors[1],
                label: $filter('escapeHtml')(key)
              });
            });

            // Create our canvas
            var canvas = document.createElement("canvas");
            canvas.height = element.height();
            canvas.width = element.width();
            element.append(canvas);

            var options = {
              percentageInnerCutout: 30
            };

            var ctx = canvas.getContext("2d");
            var donutChart = new Chart(ctx).Doughnut(dataset, options);
          });
        }
      };
    }]);


/*
 * Do a single challenge.
 */
sbDirectives.directive('challengeBox', [
    '$resource',
    '$location',
    '$rootScope',
    'answerService',
    'errorService',
    'loadingService',
    'scoreService',
    'sessionService',
    'validatorService',
    function($resource, $location, $rootscope, answerService, errorService,
      loadingService, scoreService, sessionService, validatorService) {
      return {
        restrict: 'AE',
        templateUrl: '/partials/components/challenge.html',
        scope: {
          chall: '=challenge'
        },
        link: function(scope, iElement, iAttrs) {
          var isModal = iElement.parents('.modal').length > 0;

          scope.isModal = isModal;
          scope.timer = 0;
          scope.minteams = 4
          scope.numteams = scope.minteams;

          setInterval(function() {
            scope.timer ++
          }, 1000)

          var closeModal = function(href) {
            if (isModal) {
              iElement.parents('.modal').modal('hide');
              if (href) {
                $('.modal').on('hidden.bs.modal', function(e) {
                  $location.path(href)
                  if (!$rootscope.$$phase) $rootscope.$apply()
                })
              }
            } else if (href) {
              $location.path(href)
            }
          };

          scope.closeModal = closeModal;

          scope.$watch('chall', function() {
            // Current points
            scope.currentPoints = scoreService.getCurrentPoints(scope.chall);
            // Recent solves
            scope.recent = function() {
              if (!scope.chall) return []
              var answers = scope.chall.answers.map(function(e, i) {
                e.date = (new Date(e.timestamp)).valueOf();
                return e;
              })
              answers.sort(function(a, b) {
                if (a.date < b.date) return 1
                return -1
              })
              var num = scope.numteams
              if (num < 0) {
                return answers
              }
              return answers.slice(0, num)
            }
          });

          // Setup submit handler
          scope.submitChallenge = function() {
            loadingService.start();
            errorService.clearErrors();
            var done = function() {
              loadingService.stop();
              closeModal();
            };
            if (scope.isAdmin()) {
              validatorService.create(
                {cid: scope.chall.cid, answer: scope.chall.answer},
                function(resp) {
                  errorService.error(resp.message, 'success');
                  done();
                },
                function(resp) {
                  errorService.error(resp);
                  done();
                });
              return;
            }
            answerService.create(
                {cid: scope.chall.cid, answer: scope.chall.answer},
                function(resp) {
                  scope.chall.answered = true;
                  errorService.error(
                      'Congratulations, ' + resp.points + ' points awarded!',
                      'success');
                  done();
                },
                function(resp){
                  errorService.error(resp);
                  done();
                });
          };

          scope.$watch('timer', function() {
            // Format time nicely
            scope.timeFormat = function(timestamp) {
              var time = moment(timestamp);
              var duration = moment.duration(time.diff(moment.now()))
              //Time ago in ms
              var msdiff = duration.valueOf()
              var week = 60 * 60 * 24 * 7 * 1000
              if (msdiff < week) {
                return duration.humanize(true);
              } else {
                return time.format("ddd, MMM Do")
              }
            }
          })

          // isAdmin, similar to global controller
          scope.isAdmin = function() {
            return (!!sessionService.session.user &&
                sessionService.session.user.admin);
          };
        } // Link function
      }
    }]);

sbDirectives.directive('ngAnyClick', [
    "$parse",
    function($parse) {
        return function(scope, element, attr) {
            var call = $parse(attr.ngAnyClick);
            element.bind('click', function(e) {
                scope.$apply(function() {
                    e.preventDefault();
                    call(scope, {$event:event, $click: 0});
                })
            })
            element.bind('contextmenu', function(e) {
                scope.$apply(function() {
                    e.preventDefault();
                    call(scope, {$event:event, $click: 1});
                })
            })
        }
    }])
