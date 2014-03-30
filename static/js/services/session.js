var sessionServiceModule = angular.module('sessionServiceModule', [
    'ngResource',
    'globalServices',
    ]);

sessionServiceModule.service('sessionService', [
    '$resource', '$location', 'errorService',
    function($resource, $location, errorService) {
      this.sessionData = $resource('/api/session');
      this.user = null;
      this.team = null;

      this.login = function(email, password, successCallback, errorCallback) {
        this.sessionData.save({email: email, password: password},
          angular.bind(this, function(data) {
            this.user = data.user;
            this.team = data.team;
            if (successCallback)
              successCallback();
          }), errorCallback || function() {});
      };

      this.logout = this.sessionData.remove;

      this.refresh = function(successCallback, errorCallback) {
        // Attempt to load
        this.sessionData.get(angular.bind(this, function(data) {
          this.user = data.user;
          this.team = data.team;
          if (successCallback)
            successCallback();
        }), errorCallback || function() {});
      };

      this.requireLogin = function(callback, no_redirect) {
        /* If the user is logged in, execute the callback.  Otherwise, redirect
         * to the login. */
        if (this.user !== null) {
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
