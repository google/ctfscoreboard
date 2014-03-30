var globalCtrls = angular.module('globalCtrls', [
    'globalServices',
    'sessionServiceModule',
    ]);

globalCtrls.controller('LoggedInCtrl', [
    '$scope',
    'sessionService',
    function($scope, sessionService) {
      $scope.session = sessionService.session;
      $scope.loggedIn = function(){
        return !!sessionService.session.user;
      };
      $scope.isAdmin = function(){
        return (!!sessionService.session.user &&
          sessionService.session.user.admin);
      };
    }]);

globalCtrls.controller('ErrorCtrl', [
    '$scope',
    'errorService',
    function($scope, errorService) {
      $scope.errors = errorService.errors;
    }]);
