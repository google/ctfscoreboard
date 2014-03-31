var adminChallengeCtrls = angular.module('adminChallengeCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServiceModule',
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
          errorService.error);
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
          errorService.error);
      };

      $scope.addCategory = function() {
        errorService.clearErrors();
        categoryService.create({}, $scope.newCategory,
          function(data) {
            $scope.categories.push(data);
            $scope.newCategory = {};
          },
          errorService.error);
      };

      $scope.newCategory = {};

      sessionService.requireLogin(function() {
        errorService.clearErrors();
        categoryService.get(
          function(data) {
            $scope.categories = data.categories;
          },
          errorService.error);
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
          errorService.error);
      };

      sessionService.requireLogin(function() {
        challengeService.get(function(data) {
          $scope.challenges = data.challenges;
        },
        errorService.error);
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
          errorService.error);
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
          errorService.error);
        categoryService.get(function(data) {
          $scope.categories = data.categories;
        });
      });

    }]);

adminChallengeCtrls.controller('AdminRestoreCtrl', [
    '$scope',
    'configService',
    'errorService',
    function($scope, configService, errorService) {
      $scope.config = configService.get();
    }]);

