var scoreboardApp = angular.module('scoreboardApp', [
  'ngRoute',
  'ngSanitize',
  'adminChallengeCtrls',
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
        when('/admin/challenge/:cid', {
          templateUrl: '/partials/admin/challenge.html',
          controller: 'AdminChallengeCtrl'
        }).
        when('/admin/restore/challenges', {
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
        otherwise({
          redirectTo: '/'
        });
    }]);
