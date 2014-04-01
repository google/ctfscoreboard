var scoreboardCtrls = angular.module('scoreboardCtrls', [
    'ngResource',
    'globalServices'
    ]);

scoreboardCtrls.controller('ScoreboardCtrl', [
    '$scope',
    '$resource',
    'configService',
    function($scope, $resource, configService) {
      $scope.config = configService.get();
      $resource('/api/scoreboard').get(
        function(data) {
          $scope.scoreboard = data.scoreboard;
        });
    }]);
