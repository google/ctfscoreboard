var challengeCtrls = angular.module('challengeCtrls', [
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServiceModule',
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
    '$routeParams',
    'answerService',
    'categoryService',
    'errorService',
    'sessionService',
    function($scope, $routeParams, answerService,
      categoryService, errorService, sessionService) {
      var slug = $routeParams.slug;
      errorService.clearErrors();
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
