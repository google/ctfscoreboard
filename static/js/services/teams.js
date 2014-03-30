var teamsServiceModule = angular.module('teamsServiceModule', ['ngResource']);

teamsServiceModule.service('teamsService', ['$resource',
    function($resource) {
      return $resource('api/teams/:tid');
    }]);
