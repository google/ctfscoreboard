var userServices = angular.module('userServices', ['ngResource']);

userServices.service('userService', ['$resource',
    function($resource) {
      return $resource('/api/users/:uid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'}
      });
    }]);
