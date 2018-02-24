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

/* Admin-only services */
var adminServices = angular.module('adminServices', ['ngResource']);

adminServices.service('adminStateService', [
    function() {
      this.cid = null;

      this.saveCategory = function(cat) {
        this.cid = (cat && cat.cid) || cat;
      };

      this.getCategory = function() {
        return this.cid;
      };
    }]);

adminServices.service('adminToolsService', [
    '$resource',
    function($resource) {
      this.recalculateScores = $resource('/api/tools/recalculate').save;
      this.resetScores = function(cb, err) {
        return $resource('/api/tools/reset').save(
          {op: "scores", ack: "ack"}, cb, err);
      };
      this.resetPlayers = function(cb, err) {
        return $resource('/api/tools/reset').save(
          {op: "players", ack: "ack"}, cb, err);
      };
    }]);
