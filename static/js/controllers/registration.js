var regModule = angular.module('regModule', ['sessionServiceModule']);

regModule.controller('LoginCtrl', [
    '$scope',
    '$location',
    'sessionService',
    function($scope, $location, sessionService) {
      if ($location.path().indexOf('/logout') == 0) {
        sessionService.logout();
      }
      $scope.email = '';
      $scope.password = '';
      $scope.login = function() {
        sessionService.login($scope.email, $scope.password,
          function() {
            $location.path('/challenges');
          });
      };
    }]);
