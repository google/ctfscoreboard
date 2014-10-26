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

var sbFilters = angular.module('sbFilters', []);

sbFilters.filter('markdown', [
    '$sce',
    function($sce) {
        return function(input) {
            console.log('Markdown filter called!');
            if (typeof input != "string")
                return "";
            if (typeof Markdown == "undefined" ||
                typeof Markdown.getSanitizingConverter == "undefined") {
                    console.log('Markdown not available!');
                    return input;
            }
            var converter = Markdown.getSanitizingConverter();
            return $sce.trustAsHtml(converter.makeHtml(input));
        };
    }]);

sbFilters.filter('padint',
    function() {
        return function(n, len) {
            if (!len)
                len = 2;
            else
                len = parseInt(len);
            n = '' + n;
            while(n.length < len)
                n = '0' + n;
            return n;
        };
    });
