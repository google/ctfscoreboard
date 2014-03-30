var scoreboardApp = angular.module('scoreboardApp', [
  'ngRoute',
  'sessionService'
]);

scoreboardApp.config(['$routeProvider',
    function($routeProvider) {
      $routeProvider.
        when('/login', {
          templateUrl: 'partials/login.html',
          controller: 'RegistrationCtrl'
        }).
        when('/register', {
          templateUrl: 'partials/register.html',
          controller: 'RegistrationCtrl'
        }).
        when('/challenges', {
          templateUrl: 'partials/challenges.html',
          controller: 'ChallengeCtrl'
        }).
        when('/challenges/:catSlug', {
          templateUrl: 'partials/challenges.html',
          controller: 'ChallengeCtrl'
        }).
        otherwise({
          redirectTo: '/'
        });
    }]);
