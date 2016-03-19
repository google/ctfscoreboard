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
  'adminPageCtrls',
  'adminTeamCtrls',
  'challengeCtrls',
  'globalCtrls',
  'pageCtrls',
  'regCtrls',
  'scoreboardCtrls',
  'teamCtrls',
  'sbDirectives',
  'sbFilters'
]);

scoreboardApp.config([
    '$routeProvider',
    '$locationProvider',
    function($routeProvider, $locationProvider) {
      $locationProvider.html5Mode(true);
      $routeProvider.
        when('/', {
          templateUrl: '/partials/page.html',
          controller: 'StaticPageCtrl'
        }).
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
        when('/challenges/:slug', {
          templateUrl: '/partials/challenges.html',
          controller: 'CategoryCtrl'
        }).
        when('/challenges/', {
          templateUrl: '/partials/challenge_grid.html',
          controller: 'ChallengeGridCtrl'
        }).
        when('/scoreboard', {
          templateUrl: '/partials/scoreboard.html',
          controller: 'ScoreboardCtrl'
        }).
        when('/teams/:tid', {
          templateUrl: '/partials/team.html',
          controller: 'TeamPageCtrl'
        }).
        when('/pwreset/:email/:token', {
          templateUrl: '/partials/pwreset.html',
          controller: 'PasswordResetCtrl'
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
          controller: 'AdminNewsCtrl'
        }).
        when('/admin/page/:path', {
          templateUrl: '/partials/admin/page.html',
          controller: 'AdminPageCtrl'
        }).
        otherwise({
          templateUrl: '/partials/page.html',
          controller: 'StaticPageCtrl'
        });
    }]);


scoreboardApp.run([
    '$rootScope',
    'loadingService',
    function($rootScope, loadingService) {
        $rootScope.$on('$locationChangeStart', function() {
            loadingService.start();
        });
    }]);

var getInjector = function() {
    return angular.element('*[ng-app]').injector();
};
