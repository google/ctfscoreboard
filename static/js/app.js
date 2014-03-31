var scoreboardApp = angular.module('scoreboardApp', [
  'ngRoute',
  'ngSanitize',
  'adminChallengeCtrls',
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
        otherwise({
          redirectTo: '/'
        });
    }]);
