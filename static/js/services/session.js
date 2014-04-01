var sessionServices = angular.module('sessionServices', [
    'ngResource',
    'globalServices',
    ]);

sessionServices.service('sessionService', [
    '$resource', '$location', 'errorService',
    function($resource, $location, errorService) {
      this.sessionData = $resource('/api/session');
      this.session = {
        user: null,
        team: null
      };

      this.login = function(email, password, successCallback, errorCallback) {
        this.sessionData.save({email: email, password: password},
          angular.bind(this, function(data) {
            this.session.user = data.user;
            this.session.team = data.team;
            if (successCallback)
              successCallback();
          }), errorCallback || function() {});
      };

      this.logout = function() {
        this.sessionData.remove();
        this.session.user = null;
        this.session.team = null;
      };

      this.refresh = function(successCallback, errorCallback) {
        // Attempt to load
        this.sessionData.get(angular.bind(this, function(data) {
          this.session.user = data.user;
          this.session.team = data.team;
          if (successCallback)
            successCallback();
        }), errorCallback || function() {});
      };

      this.requireLogin = function(callback, no_redirect) {
        /* If the user is logged in, execute the callback.  Otherwise, redirect
         * to the login. */
        if (this.session.user !== null) {
          return callback();
        }
        return this.refresh(callback,
            function() {
              if (no_redirect)
                return;
              errorService.error('You must be logged in.', 'info');
              $location.path('/login');
            });
      };
      this.refresh();
    }]);

function getss(){
  return angular.element(document).injector().get('sessionService');
}
