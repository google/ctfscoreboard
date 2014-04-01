var challengeServices = angular.module('challengeServices', ['ngResource']);

challengeServices.service('challengeService', ['$resource',
    function($resource) {
      return $resource('/api/challenges/:cid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'},
      });
    }]);

challengeServices.service('categoryService', ['$resource',
    function($resource) {
      this.catlist = null;

      this.res = $resource('/api/categories/:cid', {}, {
        'save': {method: 'PUT'},
        'create': {method: 'POST'},
      });

      this.get = this.res.get;
      this.create = this.res.create;
      this.save = this.res.save;
      this.delete = this.res.delete;

      this.getList = function(callback) {
        // TODO: rewrite this to maintain binding in scopes
        if (this.catlist) {
          callback(this.catlist);
          return;
        }
        this.res.get(angular.bind(this, function(data) {
          this.catlist = data;
          setTimeout(
            angular.bind(this, function() { this.catlist = null; }),
            30000);
          callback(data);
        }));
      };

    }]);

challengeServices.service('answerService', ['$resource',
    function($resource) {
      return $resource('/api/answers/:aid', {}, {
        'create': {method: 'POST'}
      });
    }]);
