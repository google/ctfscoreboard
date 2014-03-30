var regCtrls = angular.module('regCtrls', [
    'globalServices',
    'sessionServiceModule',
    'teamsServiceModule',
    'usersServiceModule'
    ]);

regCtrls.controller('LoginCtrl', [
    '$scope',
    '$location',
    'errorService',
    'sessionService',
    function($scope, $location, errorService, sessionService) {
      if ($location.path().indexOf('/logout') == 0) {
        sessionService.logout();
      }
      $scope.email = '';
      $scope.password = '';
      $scope.login = function() {
        errorService.clearErrors();
        sessionService.login($scope.email, $scope.password,
          function() {
            $location.path('/challenges');
          },
          function(errData) {
            errorService.error(errData);
          });
      };
    }]);

regCtrls.controller('RegistrationCtrl', [
    '$scope',
    '$location',
    'configService',
    'errorService',
    'sessionService',
    'teamsService',
    'usersService',
    function($scope, $location, configService, errorService, sessionService,
        teamsService, usersService) {
      $scope.config = configService.get();
      $scope.teams = teamsService.get(function() {
        $scope.teams = $scope.teams.teams;
      });
      $scope.register = function() {
        errorService.clearErrors();
        usersService.create({
          email: $scope.email,
          nick: $scope.nick,
          password: $scope.password,
          team_id: $scope.team,
          team_name: $scope.team_name,
          team_code: $scope.team_code
        }, function(data) {
          sessionService.refresh();
          $location.path('/challenges');
        }, function(errData) {
          // TODO: more verbose
          errorService.error(errData);
        });
      };
    }]);
