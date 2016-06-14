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

/* upload services */
var uploadServices = angular.module('uploadServices', ['ngResource']);

uploadServices.service('uploadService', ['$http', '$q',
    function($http, $q) {
        var basename = function(path) {
            return path.split('/').reverse()[0];
        };

        this.upload = function(file) {
            // Returns a promise with the file hash
            var filename = basename(file.name);
            // Construct the promise
            var promise = $q.defer();
            // HTTP Config
            var config = {
                transformRequest: angular.identity,
                'headers': {
                    'Content-type': undefined
                }
            };

            // Setup form data
            var fd = new FormData();
            fd.append('file', file);
            // Request
            $http.post('/api/attachment', fd, config).
                success(function(data) {
                    data.filename = filename;
                    promise.resolve(data);
                }).
                error(function(data, status) {
                    if (data)
                        promise.reject(data);
                    else
                        promise.reject('Unknown upload error.');
                });
            return promise.promise;
        };
    }]);
