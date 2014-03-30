var globalCtrls = angular.module('globalCtrls', [
    'globalServices',
    'sessionServiceModule',
    ]);

globalCtrls.controller('LoggedInCtrl', [
    '$scope',
    'sessionService',
    function($scope, sessionService) {
      $scope.loggedIn = function(){
        return !!sessionService.user;
      };
      $scope.isAdmin = function(){
        return (!!sessionService.user && sessionService.user.admin);
      };
    }]);

globalCtrls.controller('ErrorCtrl', [
    '$scope',
    'errorService',
    function($scope, errorService) {
      $scope.errors = errorService.errors;
    }]);
