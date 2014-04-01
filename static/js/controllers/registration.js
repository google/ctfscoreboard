var regCtrls = angular.module('regCtrls', [
    'globalServices',
    'sessionServices',
    'teamServices',
    'userServices'
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
    'teamService',
    'userService',
    function($scope, $location, configService, errorService, sessionService,
        teamService, userService) {
      $scope.config = configService.get();
      $scope.teams = teamService.get(function() {
        $scope.teams = $scope.teams.teams;
      });
      $scope.register = function() {
        errorService.clearErrors();
        userService.create({
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

regCtrls.controller('ProfileCtrl', [
    '$scope',
    'errorService',
    'sessionService',
    'userService',
    function($scope, errorService, sessionService, userService) {
      $scope.user = null;

      sessionService.requireLogin(function() {
        $scope.user = sessionService.user;
      });

      $scope.updateProfile = function() {
        userService.save({uid: $scope.user.uid}, $scope.user,
          function(data) {
            $scope.user = data;
            sessionService.refresh();
          },
          function(data) {
            errorService.error(data);
          });
      };
    }]);
