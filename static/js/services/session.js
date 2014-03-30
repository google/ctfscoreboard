var sessionServiceModule = angular.module('sessionServiceModule', ['ngResource']);

sessionServiceModule.service('sessionService', ['$resource',
    function($resource) {
      this.sessionData = $resource('api/session');
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

      this.refresh = function() {
        // Attempt to load
        this.sessionData.get(angular.bind(this, function(data) {
          this.user = data.user;
          this.team = data.team;
        }));
      };
      this.refresh();
    }]);

function getss(){
  return angular.element(document).injector().get('sessionService');
}
