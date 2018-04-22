/**
 * Copyright 2018 Google Inc. All Rights Reserved.
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

adminChallengeCtrls.controller('AdminTagCtrl', [
    '$scope',
    'tagService',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, tagService, errorService, sessionService, loadingService) {
      if (!sessionService.requireAdmin()) return;

      $scope.tags = [];

      $scope.updateTag = function(tag) {
        errorService.clearErrors();
        tagService.save({tagslug: tag.tagslug}, tag,
          function(data) {
            errorService.error(tag.name + ' updated.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.deleteTag = function(tag) {
        errorService.clearErrors();
        var name = tag.name;
        tagService.delete({tagslug: tag.tagslug},
          function(data) {
            var idx = $scope.tags.indexOf(tag);
            $scope.tags.splice(idx, 1);
            errorService.error(name + ' deleted.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.addTag = function() {
        errorService.clearErrors();
        tagService.create({}, $scope.newTag,
          function(data) {
            $scope.tags.push(data);
            $scope.newTag = {};
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.newTag = {};

      $scope.invalidForm = function(idx) {
          var form = $(document.getElementsByName('adminTagForm[' + idx + ']'));
          return form.hasClass('ng-invalid');
      };

      sessionService.requireLogin(function() {
        errorService.clearErrors();
        tagService.get(
          function(data) {
            $scope.tags = data.tags;
            loadingService.stop();
          },
          function(data) {
            errorService.error(data);
            loadingService.stop();
          });
      });
    }]);

adminChallengeCtrls.controller('AdminPagesCtrl', [
    '$scope',
    'pageService',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, pageService, errorService, sessionService, loadingService) {
        if (!sessionService.requireAdmin()) return;

        $scope.active = {};
        $scope.activate = function(p) {
            if (p.new == p.path) {
                $scope.active = p;
                $("#delete-confirm").modal("show");
            } else {
                var oldPath = p.path;
                p.path = p.new;
                pageService.save({path: oldPath}, p)
            }
        }

        $scope.deleteActive = function() {
            pageService.delete({path: $scope.active.path})
            $scope.pages.splice($scope.pages.indexOf($scope.active), 1)
            $scope.active = {}
        }

        sessionService.requireLogin(function() {
            errorService.clearErrors();
            pageService.get(
                function(data) {
                    $scope.pages = data.pages;
                    for (var i = 0; i < $scope.pages.length; i++) {
                        $scope.pages[i].new = $scope.pages[i].path;
                    }
                    loadingService.stop();
                },
                function(data) {
                    errorService.error(data);
                    loadingService.stop();
                });
        });
    }])

adminChallengeCtrls.controller('AdminAttachmentCtrl', [
    '$scope',
    'attachService',
    'errorService',
    'sessionService',
    'loadingService',
    'uploadService',
    function($scope, attachService, errorService, sessionService, loadingService,
        uploadService) {
      if (!sessionService.requireAdmin()) return;

      $scope.attachments = [];

      $scope.updateAttachment = function(attachment, cb) {
        errorService.clearErrors();
        attachService.save({aid: attachment.aid}, attachment,
          function(data) {
            errorService.error(attachment.filename + ' updated.', 'success');
            if (cb) cb(data);
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.deleteAttachment = function(attachment) {
        errorService.clearErrors();
        var filename = attachment.filename;
        attachService.delete({aid: attachment.aid},
          function(data) {
            var idx = $scope.attachments.indexOf(attachment);
            $scope.attachments.splice(idx, 1);
            errorService.error(name + ' deleted.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };


      $scope.addAttachment = function() {
          $scope.newAttachment.challenges = $scope.newAttachment.challenges || [];
          $scope.updateAttachment($scope.newAttachment, function(data) {
              $scope.newAttachment = {};
              for (var i = 0; i < $scope.attachments.length; i++) {
                  if ($scope.attachments[i].aid == data.aid) return;
              }
              $scope.attachments.push(data);
          });
      }

      $scope.newAttachment = {};

      $scope.invalidForm = function(idx) {
          var form = $(document.getElementsByName('adminAttachmentForm[' + idx + ']'));
          return form.hasClass('ng-invalid');
      };

      $scope.replace = function(a) {
        uploadService.request().then(uploadService.upload).then(function(newfile) {
          if (a.aid == newfile.aid) return;
          attachService.delete({aid: a.aid});
          a.aid = newfile.aid;
          attachService.save({aid: a.aid}, a, function(d) {}, function(e) {
            console.error(e);
          })
        });
      }

      $scope.addfile = function() {
        uploadService.request().then(uploadService.upload).then(function(newfile) {
          $scope.newAttachment.aid = newfile.aid;
        })
      }

      sessionService.requireLogin(function() {
        errorService.clearErrors();
        attachService.get(
          function(data) {
            $scope.attachments = data.attachments;
            loadingService.stop();
          },
          function(data) {
            errorService.error(data);
            loadingService.stop();
          });
      });
    }]);


adminChallengeCtrls.controller('AdminChallengesCtrl', [
    '$scope',
    '$filter',
    '$location',
    '$routeParams',
    'challengeService',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, $filter, $location, $routeParams, challengeService,
        errorService, sessionService, loadingService) {
      if (!sessionService.requireAdmin()) return;

      var updateChallenges = function(challenges) {
        $scope.challenges = $filter('orderBy')(challenges,
            function(item) {
              return item.weight;
            });
      };

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

      $scope.newChallenge = function() {
        $location.path('/admin/challenge');
      };

      // Ordering things
      var swapChallenges = function(idx, offset) {
        var temp = $scope.challenges[idx];
        $scope.challenges[idx] = $scope.challenges[idx + offset];
        $scope.challenges[idx + offset] = temp;
        $scope.weightsChanged = true;
      };
      $scope.moveUp = function(challenge) {
        var idx = $scope.challenges.indexOf(challenge);
        if (idx < 1) {
          console.log('Attempt to moveUp non-existent or first item.');
          return;
        }
        swapChallenges(idx, -1);
      };
      $scope.moveDown = function(challenge) {
        var idx = $scope.challenges.indexOf(challenge);
        if (idx > ($scope.challenges.length - 1) || idx == -1) {
          console.log('Attempt to moveDown non-existent or last item.');
          return;
        }
        swapChallenges(idx, 1);
      };
      $scope.weightsChanged = false;
      $scope.saveBulk = function() {
        loadingService.start();
        var failed = false;
        // Set new weights
        var weight = 0;
        // Make a copy to avoid overwriting other challenge updates
        challengeService.get(function(data) {
          angular.forEach($scope.challenges, function(mod_chall) {
            weight += 1;
            angular.forEach(data.challenges, function(chall) {
              if (mod_chall.cid == chall.cid) {
                if (weight == chall.weight)
                  return;
                chall.weight = weight;
                challengeService.save({cid: chall.cid},
                    chall,
                    function() {},
                    function(data) {
                      failed = true;
                      errorService.error(data);
                    });
              }
            });
          });
          updateChallenges(data.challenges);
          loadingService.stop();
        },
        function (data) {
          errorService.error(data);
          loadingService.stop();
        });
      };

      sessionService.requireLogin(function() {
        challengeService.get(function(data) {
          updateChallenges(data.challenges);
          loadingService.stop();
        },
        function(data) {
          errorService.error(data);
          loadingService.stop();
        });
      });
    }]);

adminChallengeCtrls.controller('AdminChallengeCtrl', [
    '$scope',
    '$location',
    '$routeParams',
    'challengeService',
    'errorService',
    'sessionService',
    'uploadService',
    'loadingService',
    'tagService',
    'attachService',
    'configService',
    function($scope, $location, $routeParams, challengeService, errorService,
      sessionService, uploadService, loadingService, tagService, attachService,
      configService) {
      if (!sessionService.requireAdmin()) return;

      $scope.cid = $routeParams.cid;
      $scope.newAttachment = {};
      $scope.addNewAttachment = false;
      $scope.action = 'New';
      $scope.editing = false;  // New or editing?
      $scope.config = configService.get();

      var goEdit = function() {
        $scope.action = 'Edit';
        $scope.answerPlaceholder = 'Enter answer; leave blank to ' +
          'leave unchanged.';
        $scope.editing = true;
        if (!$routeParams.cid) {
          $location.path($location.path() + '/' + $scope.challenge.cid);
          $scope.cid = $scope.challenge.cid;
        }
      };

      $scope.saveChallenge = function() {
        errorService.clearErrors();
        // TODO: Check attachments

        if ($scope.challenge.prerequisite && (
          $scope.challenge.prerequisite.type == 'None')) {
          $scope.challenge.prerequisite = null;
        };

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
            goEdit();
            errorService.error('Saved.', 'success');
          },
          function(data) {
            errorService.error(data);
          });
      };

      $scope.attachmentType = 'new';

      attachService.get(function(data) {
        $scope.allAttachments = data.attachments;
        $scope.updateAttachments();
      }, function(e) {
        errorService.error(e);
      })

      var setSubtract = function(a, b, key) {
        if (!a) return b;
        if (!b) return [];
        var isIn = function(val) {
          for (var i = 0; i < a.length; i++) {
            if (a[i][key] == val) return true;
          }
          return false;
        }
        var out = []
        for (var i = 0; i < b.length; i++) {
          if (!isIn(b[i][key])) {
            out.push(b[i]);
          }
        }
        return out;
      };

      $scope.updateAttachments = function () {
        if (!$scope.challenge) return;
        $scope.attachments = setSubtract(
          $scope.challenge.attachments, $scope.allAttachments, 'aid');
        $scope.attachmentType = 'new';
      };

      $scope.$watch('challenge.attachments', $scope.updateAttachments, true);

      var addAttachment = function(aid) {
        for (var i = 0; i < $scope.attachments.length; i++) {
          if ($scope.attachments[i].aid == aid) {
            $scope.challenge.attachments.push($scope.attachments[i]);
            return;
          }
        }
        errorService.error('Could not add attachment: '+aid);
      };

      $scope.addAttachment = function() {
        if ($scope.attachmentType == 'new') {
          uploadService.request().then(uploadService.upload).then(function (data) {
            $scope.challenge.attachments.push(data);
          })
        } else {
          addAttachment($scope.attachmentType);
        }
      };

      $scope.verifyFile = function() {
          // Verify existance by hash
          // TODO
      };

      $scope.deleteAttachment = function(attachment) {
        var idx = $scope.challenge.attachments.indexOf(attachment);
        $scope.challenge.attachments.splice(idx, 1);
      };

      // Prerequisite handlers
      $scope.updatePrerequisite = function() {
        var type = $scope.challenge.prerequisite.type || 'None';
        if (type == 'None')
          return;
        if (type == 'solved') {
          // Load the challenge list
          loadingService.start();
          challengeService.get(function(data) {
            $scope.challengeList = [];
            angular.forEach(data.challenges, function(c) {
              $scope.challengeList.push({'cid': c.cid, 'name': c.name});
            })
            loadingService.stop();
          }, function(data) {
            errorService.error(data);
            loadingService.stop();
          });
        }
      };

      $scope.hasTag = function(tag) {
        if (!$scope.challenge) {
          return false;
        }
        for (var i = 0; i < $scope.challenge.tags.length; i++) {
          if (tag == $scope.challenge.tags[i].tagslug) {
            return true;
          }
        }
        return false;
      }

      $scope.toggleTag = function(tagslug) {
        for (var i = 0; i < $scope.challenge.tags.length; i++) {
          if ($scope.challenge.tags[i].tagslug == tagslug) {
            $scope.challenge.tags.splice(i,1);
            return;
          }
        }
        for (var i = 0; i < $scope.tags.length; i++) {
          if ($scope.tags[i].tagslug == tagslug) {
            $scope.challenge.tags.push($scope.tags[i]);
            return;
          }
        }
      }

      /* Setup on load */
      sessionService.requireLogin(function() {
        if ($routeParams.cid) {
          // Editing
          challengeService.get({cid: $routeParams.cid},
            function(data) {
                $scope.challenge = data;
                goEdit();
                $scope.updatePrerequisite();
                loadingService.stop();
            },
            function(data) {
                errorService.error(data);
                loadingService.stop();
            });
        } else {
            // New
            $scope.challenge = {
                'tags': [],
                'attachments': [],
                'prerequisite': {
                  'type': 'None'
                },
                'validator': 'static_pbkdf2'
            };
        }
        tagService.getList(function(data) {
          $scope.tags = data.tags;
        });
        loadingService.stop();
      });

    }]);

adminChallengeCtrls.controller('AdminRestoreCtrl', [
    '$scope',
    '$resource',
    'errorService',
    'sessionService',
    'loadingService',
    function($scope, $resource, errorService, sessionService, loadingService) {
      if (!sessionService.requireAdmin()) return;

      $scope.replace = false;
      $scope.ready = false;
      $scope.fileData = null;
      $scope.fileName = 'No file chosen.';

      $scope.chooseRestoreFile = function() {
        $scope.ready = false;
        $('#restore-file-chooser').click();
      };

      var fileChooserChange = function(evt) {
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
              if (contents.substr(0,6) == ")]}',\n")
                contents = contents.substr(6);
              $scope.fileData = angular.fromJson(contents);
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
      };

      $('#restore-file-chooser').change(fileChooserChange);
      $scope.$on('$destroy', function() {
        $('#restore-file-chooser').unbind('change', fileChooserChange);
      });

      $scope.submitRestore = function() {
        if (!$scope.ready) {
          // Shouldn't even be here!
          errorService.error('Not ready to submit!');
          return;
        }
        $resource('/api/backup').save({}, {
          challenges: $scope.fileData.challenges,
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
      loadingService.stop();
    }]);

