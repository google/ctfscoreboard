var teamServices = angular.module('teamServices', ['ngResource']);

teamServices.service('teamService', ['$resource',
    function($resource) {
      return $resource('/api/teams/:tid', {}, {
        save: {method: 'PUT'},
        create: {method: 'POST'}
        });
    }]);
