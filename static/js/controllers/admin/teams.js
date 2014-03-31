var adminTeamCtrls = angular.module('adminTeamCtrls', [
    'ngResource',
    'ngRoute',
    'globalServices',
    'sessionServiceModule',
    'teamServices',
    'userServices'
    ]);

adminTeamCtrls.controller('AdminTeamsCtrl', [
    '$scope',
    '$routeParams',
    'sessionService',
    'teamsService',
    function($scope, $routeParams, sessionService, teamsService) {
      $scope.teams = [];
      $scope.team = null;

      $scope.updateTeam = function() {
      };

      sessionService.requireLogin(function() {
        var tid = $routeParams.tid;
        if (tid) {
          $scope.team = teamsService.get({tid: tid});
        } else {
          teamsService.get(function(data) {
            $scope.teams = data.teams;
          });
        }
      });
    }]);

adminTeamCtrls.controller('AdminUsersCtrl', [
    '$scope',
    '$routeParams',
    'configService',
    'sessionService',
    'teamsService',
    'usersService',
    function($scope, $routeParams, configService, sessionService, teamsService, usersService) {
      $scope.users = [];
      $scope.teams = [];
      $scope.user = null;
      $scope.config = configService.get();

      $scope.updateUser = function() {
      };

      $scope.getTeam = function(user) {
        var team;
        angular.forEach($scope.teams, function(v) {
          if (v.tid == user.team) {
            team = v;
          }
        });
        return team;
      };

      sessionService.requireLogin(function() {
        teamsService.get(function(data) {
          $scope.teams = data.teams;
          var uid = $routeParams.uid;
          if (uid) {
            $scope.user = usersService.get({uid: uid});
          } else {
            usersService.get(function(data) {
              $scope.users = data.users;
            });
          }
        });
      });
    }]);
