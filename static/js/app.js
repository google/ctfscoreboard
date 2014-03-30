var scoreboardApp = angular.module('scoreboardApp', [
  'ngRoute',
  'ngSanitize',
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
        when('/challenges', {
          templateUrl: '/partials/challenges.html',
          controller: 'ChallengeCtrl'
        }).
        when('/challenges/:slug', {
          templateUrl: '/partials/challenges.html',
          controller: 'ChallengeCtrl'
        }).
        when('/scoreboard', {
          templateUrl: '/partials/scoreboard.html',
          controller: 'ScoreboardCtrl'
        }).
        otherwise({
          redirectTo: '/'
        });
    }]);
