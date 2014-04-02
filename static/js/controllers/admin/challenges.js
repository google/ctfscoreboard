var adminChallengeCtrls = angular.module('adminChallengeCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServices',
    ]);

adminChallengeCtrls.controller('AdminCategoryCtrl', [
    '$scope',
    'categoryService',
    'errorService',
    'sessionService',
    function($scope, categoryService, errorService, sessionService) {
      $scope.categories = [];

      $scope.updateCategory = function(cat) {
        errorService.clearErrors();
        categoryService.save({cid: cat.cid}, cat,
          function(data) {
            errorService.error(cat.name + ' updated.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.deleteCategory = function(cat) {
        errorService.clearErrors();
        var name = cat.name;
        categoryService.delete({cid: cat.cid},
          function(data) {
            // remove from scope
            var idx = $scope.categories.indexOf(cat);
            $scope.categories.splice(idx, 1);
            errorService.error(name + ' deleted.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.addCategory = function() {
        errorService.clearErrors();
        categoryService.create({}, $scope.newCategory,
          function(data) {
            $scope.categories.push(data);
            $scope.newCategory = {};
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.newCategory = {};

      sessionService.requireLogin(function() {
        errorService.clearErrors();
        categoryService.get(
          function(data) {
            $scope.categories = data.categories;
          },
          function(data) {
            errorService.error(data);
          });
      });
    }]);

adminChallengeCtrls.controller('AdminChallengesCtrl', [
    '$scope',
    '$routeParams',
    'challengeService',
    'errorService',
    'sessionService',
    function($scope, $routeParams, challengeService, errorService, sessionService) {
      $scope.catid = $routeParams.cid;

      $scope.lockChallenge = function(challenge, locked) {
        var copy = {};
        angular.forEach(challenge, function(v, k) {
          copy[k] = v;
        });
        copy.unlocked = !locked;
        challengeService.save({cid: challenge.cid},
          copy,
          function(data) {
            challenge.unlocked = data.unlocked;
          },
          function(data) {
            errorService.error(data);
          });
      };

      sessionService.requireLogin(function() {
        challengeService.get(function(data) {
          $scope.challenges = data.challenges;
        },
        function(data) {
          errorService.error(data);
        });
      });
    }]);

adminChallengeCtrls.controller('AdminChallengeCtrl', [
    '$scope',
    '$routeParams',
    'categoryService',
    'challengeService',
    'errorService',
    'sessionService',
    function($scope, $routeParams, categoryService, challengeService,
      errorService, sessionService) {
      $scope.cid = $routeParams.cid;

      $scope.saveChallenge = function() {
        errorService.clearErrors();
        $scope.challenge.$save({cid: $scope.challenge.cid},
          function(data) {
            $scope.challenge = data;
            errorService.error('Saved.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.addHint = function() {
        $scope.challenge.hints.push({});
      };

      $scope.deleteHint = function(hint) {
        var idx = $scope.challenge.hints.indexOf(hint);
        $scope.challenge.hints.splice(idx, 1);
      };

      sessionService.requireLogin(function() {
        challengeService.get({cid: $routeParams.cid},
          function(data) {
            $scope.challenge = data;
          },
          function(data) {
            errorService.error(data);
          });
        categoryService.get(function(data) {
          $scope.categories = data.categories;
        });
      });

    }]);

adminChallengeCtrls.controller('AdminRestoreCtrl', [
    '$scope',
    '$resource',
    'errorService',
    function($scope, $resource, errorService) {
      $scope.replace = false;
      $scope.ready = false;
      $scope.fileData = null;
      $scope.fileName = 'No file chosen.';

      $scope.chooseRestoreFile = function() {
        $scope.ready = false;
        $('#restore-file-chooser').click();
      };

      $('#restore-file-chooser').change(function(evt) {
        $scope.$apply(function() {
          var file = evt.target.files[0];
          if (!file) {
            $scope.fileName = 'No file chosen.';
            return;
          }
          $scope.fileName = file.name;
          var reader = new FileReader();
          reader.onload = function(e) {
            $scope.$apply(function() {
              var contents = e.target.result;
              $scope.fileData = $.parseJSON(contents);
              $scope.ready = true;
            });
          };
          reader.onerror = function(e) {
            $scope.$apply(function() {
              errorService.error('Failed to load file!');
            });
          };
          reader.readAsText(file);
        });
      });

      $scope.submitRestore = function() {
        if (!$scope.ready) {
          // Shouldn't even be here!
          errorService.error('Not ready to submit!');
          return;
        }
        $resource('/api/backup').save({}, {
          categories: $scope.fileData.categories,
          replace: $scope.replace
        },
        function(data) {
          errorService.error(data.message, 'success');
          var chooser = $('#restore-file-chooser');
          chooser.replaceWith(chooser.clone(true));
        },
        function(data) {
          errorService.error(data);
        });
      };
    }]);

