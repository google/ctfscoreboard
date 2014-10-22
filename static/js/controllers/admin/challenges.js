/**
 * Copyright 2014 David Tomaschik <david@systemoverlord.com>
 * 
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *    http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

var adminChallengeCtrls = angular.module('adminChallengeCtrls', [
    'ngResource',
    'ngRoute',
    'challengeServices',
    'globalServices',
    'sessionServices',
    'uploadServices',
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

      $scope.deleteChallenge = function(challenge) {
          var name = challenge.name;
          challengeService.delete({cid: challenge.cid},
            function(){
                var idx = $scope.challenges.indexOf(challenge);
                $scope.challenges.splice(idx, 1);
                errorService.error(name + ' deleted.', 'success');
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
    'uploadService',
    function($scope, $routeParams, categoryService, challengeService,
      errorService, sessionService, uploadService) {
      $scope.cid = $routeParams.cid;
      $scope.newAttachment = {};
      $scope.addNewAttachment = false;

      $scope.saveChallenge = function() {
        errorService.clearErrors();
        // Check attachments

        var save_func;
        if ($scope.challenge.cid) {
            save_func = challengeService.save;
        } else {
            save_func = challengeService.create;
        }
        save_func({cid: $scope.challenge.cid},
          $scope.challenge,
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

      $scope.addAttachment = function() {
          $scope.newAttachment = {};
          $scope.addNewAttachment = true;
      };

      $scope.uploadFile = function() {
          // Upload file and get hash
          var fileField = $('#upload-new');
          var file = fileField.get(0).files[0];

          if (!file) {
              errorService.error('Must select a file.');
              return;
          }

          uploadService.upload(file).then(
            function(metadata) {
                $scope.challenge.attachments.push(metadata);
                $scope.newAttachment = {};
                $scope.addNewAttachment = false;
                fileField.replaceWith(fileField.clone(true));
            }, function(data) {
                errorService.error(data);
            });
      };

      $scope.verifyFile = function() {
          // Verify existance by hash
          // TODO
      };

      $scope.deleteAttachment = function(attachment) {
        var idx = $scope.challenge.attachments.indexOf(attachment);
        $scope.challenge.attachments.splice(idx, 1);
      };

      /* Setup on load */
      sessionService.requireLogin(function() {
        if ($routeParams.cid) {
          challengeService.get({cid: $routeParams.cid},
            function(data) {
                $scope.challenge = data;
            },
            function(data) {
                errorService.error(data);
            });
        } else {
            $scope.challenge = {'hints': []};
        }
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

