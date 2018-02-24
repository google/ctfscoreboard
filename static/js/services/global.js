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

/* Global services */
var globalServices = angular.module('globalServices', ['ngResource']);

globalServices.service('configService', [
    '$resource',
    function($resource) {
      return $resource('/api/config', {}, {
        'get': {cache: true}
      });
    }]);


globalServices.service('errorService',
    function() {
      var inhibit = false;
      this.errors = [];

      this.clearErrors = angular.bind(this, function() {
        if (inhibit) {
          inhibit = false;
          return;
        }
        this.errors.length = 0;
      });

      this.error = angular.bind(this, function(msg, severity) {
        severity = severity || 'danger';
        if (typeof msg == "object") {
          msg = (msg.data && msg.data.message) || msg.message || "Request Error";
        }
        this.errors.push({severity: severity, msg: msg});
      });

      this.success = angular.bind(this, function(msg) {
        this.error(msg, 'success');
      });

      this.inhibitClear = function() {
        inhibit = true;
      };

      this.clearAndInhibit = angular.bind(this, function() {
        inhibit = false;
        this.clearErrors();
        this.inhibitClear();
      });
    });


globalServices.service('proofOfWorkService', [
  'configService',
  function(configService) {
    //angular.injector(['globalServices']).get('proofOfWorkService')
    var subtle = window.crypto.subtle;

    // Returns a promise with the key
    this.proofOfWork = function(instr) {
      return new Promise(function(resolve, reject) {
        configService.get(function(cfg) {
          var nbits = cfg.proof_of_work_bits;
          if (nbits == 0) {
            resolve('');
            return;
          }
          _proofOfWork(instr, nbits).then(resolve).catch(reject);
        });
      });
    };

    // Internal implementation
    var _proofOfWork = function(instr, nbits) {
      var start = Date.now();
      return new Promise(function(resolve, reject) {
        var resolver = function(k) {
          var end = Date.now();
          console.log('Proof of work took ' + (end - start) + ' ms');
          resolve(k);
        };
        // Sortof recursive -- not great, but best I can come up.
        // Patches welcome.
        var callTry = function() {
          return _tryProofOfWork(instr, nbits)
              .then(resolver).catch(callTry);
        };
        callTry();
      });
    };

    // HMAC with random key
    // Promise is fulfilled with args (key, signature)
    var _hmacRandom = function(instr) {
      var buf = new TextEncoder("utf-8").encode(instr);
      return new Promise(function(resolve, reject) {
        subtle.generateKey(
          {
            name: 'HMAC',
            hash: {name: 'SHA-256'},
            length: 256
          },
          true,
          ['sign'])
          .then(function(key) {
            subtle.sign(
              {name: 'HMAC'},
              key,
              buf
            )
            .then(function(signature) {
              resolve({key: key, signature: new Uint8Array(signature)});
            })
            .catch(reject);
          })
          .catch(reject);
      });
    };

    var testbits = function(arr, nbits) {
      while (nbits >= 8) {
        if (arr[0] != 0)
          return false;
        nbits -= 8;
        arr = arr.slice(1);
      }
      var mask = 2**nbits - 1;
      return ((arr[0] & mask) == 0);
    };

    // Try to find a key with low bits set to 0
    var _tryProofOfWork = function(instr, nbits) {
      return new Promise(function(resolve, reject) {
        _hmacRandom(instr)
        .then(function(params) {
          if (testbits(params.signature, nbits)) {
            subtle.exportKey('jwk', params.key)
            .then(function(k) {
              resolve(k.k);
            })
            .catch(reject);
          } else {
            reject('');
          }
        })
        .catch(reject);
      });
    };

    // Useful for tuning
    window._proofOfWork = _proofOfWork;
  }]);


globalServices.service('loadingService', [
    '$timeout',
    function($timeout) {
        // Basically just keeps a loading flag
        var loading = false;
        var loadTimer = null;
        var debounce = 250;  // Debounce ms

        this.getState = function() {
            return loading;
        };
        this.start = function() {
            if (loadTimer || loading)
                return;
            loadTimer = $timeout(
                function() {
                    loading = true;
                }, debounce);
        };
        this.end = function() {
            if (loadTimer) {
                $timeout.cancel(loadTimer);
                loadTimer = null;
            }
            loading = false;
        };
        this.stop = this.end;
    }]);


globalServices.service('gameTimeService', [
    '$q',
    'configService',
    'errorService',
    function($q, configService, errorService) {
        var future = $q.defer();
        this.start = null;
        this.end = null;

        configService.get(
            angular.bind(this, function(config) {
                this.start = config.game_start && Date.parse(config.game_start);
                this.end = config.game_end && Date.parse(config.game_end);
                future.resolve();
            }),
            function(data) {
                errorService.error(data);
            });

        this.toStart = function() {
            // Time in seconds to start of game, or null if no start specified
            if (!this.start)
                return null;
            return Math.round((this.start - Date.now()) / 1000);
        };

        this.toEnd = function() {
            // Time in seconds to end of game, or null if no end specified
            if (!this.end)
                return null;
            return Math.round((this.end - Date.now()) / 1000);
        };

        this.duringGame = function(opt_callback) {
            // Return true or execute callback if in the game
            if (this.start != null && this.toStart() > 0)
                return false;
            if (this.end != null && this.toEnd() < 0)
                return false;
            if (opt_callback)
                return opt_callback();
            return true;
        };

        this.started = angular.bind(this, function() {
            return !this.start || this.toStart() < 0
        })

        this.then = function(callback) {
          future.promise.then(callback);
        };
    }]);


globalServices.service('newsService', [
    '$resource',
    '$interval',
    'configService',
    function($resource, $interval, configService) {
        this.newsResource = $resource('/api/news');
        this.get = this.newsResource.get;
        this.query = this.newsResource.query;
        this.save = this.newsResource.save;
        this.pollPromise_ = undefined;
        this.inFlight_ = false;

        // Callbacks to be called on new news
        this.clients_ = [];
        this.registerClient = function(client) {
            this.clients_.push(client);
        };

        // Polling handler
        this.poll = function() {
            if (this.inFlight_)
                return;
            this.inFlight_ = true;
            this.newsResource.query(angular.bind(this, function(data) {
                angular.forEach(this.clients_, function(cb) {
                    cb(data);
                });
                this.inFlight_ = false;
            }), angular.bind(this, function() { this.inFlight_ = false }));
        };

        // Set up polling
        this.start = function() {
            if (this.pollPromise_)
                return;
            this.poll();
            configService.get(angular.bind(this, function(config) {
                if (config.news_mechanism != 'poll')
                    return;
                var interval = config.news_poll_interval || 60000;  // 60 seconds
                this.pollPromise_ = $interval(angular.bind(this, this.poll), interval);
            }));
        };

        // Shutdown
        this.stop = function() {
            $interval.cancel(this.pollPromise_);
            this.pollPromise_ = undefined;
        };
    }]);
