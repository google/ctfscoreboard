/**
 * Copyright 2016 Google Inc. All Rights Reserved.
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

/* page services */
var pageServices = angular.module('pageServices', ['ngResource']);

pageServices.service('pageService', [
    '$resource',
    '$location',
    function($resource, $location) {
        this.resource = $resource('/api/page/:path');
        this.get = this.resource.get;
        this.save = this.resource.save;

        /** Return path to page with prefix stripped. */
        this.pagePath = function(prefix) {
            prefix = prefix || '/';
            var path = $location.path();
            if (path.substr(0, prefix.length) == prefix) {
                path = path.substr(prefix.length);
            }
            return path;
        };
    }]);
