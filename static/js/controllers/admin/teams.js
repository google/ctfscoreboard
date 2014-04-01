var adminTeamCtrls = angular.module('adminTeamCtrls', [
    'ngResource',
    'ngRoute',
    'globalServices',
    'sessionServices',
    'teamServices',
    'userServices'
    ]);

adminTeamCtrls.controller('AdminTeamsCtrl', [
    '$scope',
    '$routeParams',
    'errorService',
    'sessionService',
    'teamService',
    function($scope, $routeParams, errorService, sessionService, teamService) {
      $scope.teams = [];
      $scope.team = null;

      $scope.updateTeam = function() {
        errorService.clearErrors();
        $scope.team.$save({tid: $scope.team.tid},
          function(data) {
            $scope.team = data;
            errorService.error('Saved.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      sessionService.requireLogin(function() {
        var tid = $routeParams.tid;
        if (tid) {
          $scope.team = teamService.get({tid: tid});
        } else {
          teamService.get(function(data) {
            $scope.teams = data.teams;
          });
        }
      });
    }]);

adminTeamCtrls.controller('AdminUsersCtrl', [
    '$scope',
    '$routeParams',
    'configService',
    'errorService',
    'sessionService',
    'teamService',
    'userService',
    function($scope, $routeParams, configService, errorService, sessionService,
      teamService, userService) {
      $scope.users = [];
      $scope.teams = [];
      $scope.user = null;
      $scope.config = configService.get();

      $scope.updateUser = function() {
        errorService.clearErrors();
        $scope.user.$save({uid: $scope.user.uid},
          function(data) {
            $scope.user = data;
            errorService.error('Saved.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      var getTeam = function(tid) {
        var team = null;
        angular.forEach($scope.teams, function(t) {
          if (t.tid == tid) {
            team = t;
          }
        });
        return team;
      };

      sessionService.requireLogin(function() {
        teamService.get(function(data) {
          $scope.teams = data.teams;
          var uid = $routeParams.uid;
          if (uid) {
            $scope.user = userService.get({uid: uid},
              function() {
                $scope.user.team = getTeam($scope.user.team_tid);
              });
          } else {
            userService.get(function(data) {
              $scope.users = data.users;
              angular.forEach($scope.users, function(u) {
                u.team = getTeam(u.team_tid);
              });
            });
          }
        });
      });  // end requireLogin block
    }]);
