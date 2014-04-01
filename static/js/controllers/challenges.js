var challengeCtrls = angular.module('challengeCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServices',
    ]);

challengeCtrls.controller('CategoryMenuCtrl', [
    '$scope',
    'categoryService',
    'sessionService',
    function($scope, categoryService, sessionService) {
      sessionService.requireLogin(function() {
        categoryService.getList(function(data) {
          $scope.categories = data.categories;
        });
      }, true);
    }]);

challengeCtrls.controller('ChallengeCtrl', [
    '$scope',
    '$resource',
    '$routeParams',
    'answerService',
    'categoryService',
    'errorService',
    'sessionService',
    function($scope, $resource, $routeParams, answerService,
      categoryService, errorService, sessionService) {
      errorService.clearErrors();

      $scope.filterUnlocked = function(chall) {
        return chall.unlocked == true;
      };

      var slug = $routeParams.slug;
      if (slug) {
        $scope.submitChallenge = function(chall) {
          errorService.clearErrors();
          answerService.create({cid: chall.cid, answer: chall.answer},
            function(resp) {
              chall.answered = true;
              errorService.error(
                'Congratulations, ' + resp.points + 'awarded!',
                'success');
            },
            function(resp) {
              errorService.error(resp);
            });
        };

        $scope.unlockHintDialog = function(hint) {
          errorService.clearErrors();
          $scope.hint = hint;
          $('#hint-modal').modal('show');
        };

        $scope.unlockHint = function(hint) {
          $resource('/api/unlock_hint').save({hid: hint.hid},
              function(data) {
                hint.hint = data.hint;
                errorService.error(
                  'Unlocked hint for ' + hint.cost + ' points.',
                  'success');
                $('#hint-modal').modal('hide');
              },
              function(data) {
                errorService.error(data);
                $('#hint-modal').modal('hide');
              });
        };

        // Load challenges
        sessionService.requireLogin(function() {
          var found = false;
          categoryService.getList(function(data) {
            angular.forEach(data.categories, function(c) {
              if (c.slug == slug){
                categoryService.get({cid: c.cid},
                  function(cat) {
                    $scope.category = cat;
                    $scope.category.answers = {};
                    $scope.challenges = cat.challenges;
                  });
                found = true;
              }
            });
            if (!found) {
              errorService.error('Category not found.');
            }
          });
        });
      }
    }]);
