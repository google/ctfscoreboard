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

      this.clearErrors = function() {
        if (inhibit) {
          inhibit = false;
          return;
        }
        this.errors.length = 0;
      };

      this.error = function(msg, severity) {
        severity = severity || 'danger';
        msg = (msg.data && msg.data.message) || msg.message || msg.data || msg;
        this.errors.push({severity: severity, msg: msg});
      };

      this.success = function(msg) {
        this.error(msg, 'success');
      };

      this.inhibitClear = function() {
        inhibit = true;
      };

      this.clearAndInhibit = function() {
        inhibit = false;
        this.clearErrors();
        this.inhibitClear();
      };
    });


globalServices.service('loadingService',
    function() {
        // Basically just keeps a loading flag
        var loading = false;
        this.getState = function() {
            return loading;
        };
        this.start = function() {
            loading = true;
        };
        this.end = function() {
            loading = false;
        };
        this.stop = this.end;
    });


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

        this.then = future.promise.then;
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
