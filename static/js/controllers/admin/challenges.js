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
