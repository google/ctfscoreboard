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

var scoreboardApp = angular.module('scoreboardApp', [
  'ngRoute',
  'ngSanitize',
  'adminChallengeCtrls',
  'adminNewsCtrls',
  'adminTeamCtrls',
  'challengeCtrls',
  'globalCtrls',
  'regCtrls',
  'scoreboardCtrls'
]);

scoreboardApp.config([
    '$routeProvider',
    '$locationProvider',
    function($routeProvider, $locationProvider) {
      $locationProvider.html5Mode(true);
      $routeProvider.
        when('/login', {
          templateUrl: '/partials/login.html',
          controller: 'LoginCtrl'
        }).
        when('/logout', {
          templateUrl: '/partials/login.html',
          controller: 'LoginCtrl'
        }).
        when('/register', {
          templateUrl: '/partials/register.html',
          controller: 'RegistrationCtrl'
        }).
        when('/profile', {
          templateUrl: '/partials/profile.html',
          controller: 'ProfileCtrl'
        }).
        when('/challenges/:slug?', {
          templateUrl: '/partials/challenges.html',
          controller: 'ChallengeCtrl'
        }).
        when('/scoreboard', {
          templateUrl: '/partials/scoreboard.html',
          controller: 'ScoreboardCtrl'
        }).
        when('/admin/categories', {
          templateUrl: '/partials/admin/categories.html',
          controller: 'AdminCategoryCtrl'
        }).
        when('/admin/challenges/:cid?', {
          templateUrl: '/partials/admin/challenges.html',
          controller: 'AdminChallengesCtrl'
        }).
        when('/admin/challenge/:cid?', {
          templateUrl: '/partials/admin/challenge.html',
          controller: 'AdminChallengeCtrl'
        }).
        when('/admin/backups', {
          templateUrl: '/partials/admin/restore.html',
          controller: 'AdminRestoreCtrl'
        }).
        when('/admin/teams/:tid?', {
          templateUrl: '/partials/admin/teams.html',
          controller: 'AdminTeamsCtrl'
        }).
        when('/admin/users/:uid?', {
          templateUrl: '/partials/admin/users.html',
          controller: 'AdminUsersCtrl'
        }).
        when('/admin/news', {
          templateUrl: '/partials/admin/news.html',
          controller: 'AdminNewsCtrl',
        }).
        otherwise({
          redirectTo: '/'
        });
    }]);
