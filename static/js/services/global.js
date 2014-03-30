/* Global services */
var globalServices = angular.module('globalServices', ['ngResource']);

globalServices.service('configService', ['$resource',
    function($resource) {
      return $resource('/api/config', {}, {
        'get': {cached: true}
      });
    }]);

globalServices.service('errorService',
    function() {
      this.errors = [];
      this.clearErrors = function() {
        this.errors.length = 0;
      };
      this.error = function(msg, severity) {
        severity = severity || 'danger';
        msg = (msg.data && msg.data.message) || msg.data || msg;
        this.errors.push({severity: severity, msg: msg});
      };
    });

