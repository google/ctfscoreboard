var usersServiceModule = angular.module('usersServiceModule', ['ngResource']);

usersServiceModule.service('usersService', ['$resource',
    function($resource) {
      return $resource('/api/users/:uid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'}
      });
    }]);
