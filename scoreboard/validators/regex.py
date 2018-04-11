# Copyright 2018 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re

from scoreboard.validators import base


class RegexValidator(base.BaseValidator):
    """Regex-based validator.

    Note that validation based on a regex is inherently subject to timing
    attacks.  If this is important to you, you should use a validator like
    static_pbkdf2.
    """

    name = 'Regular Expression'
    re_flags = 0

    def validate_answer(self, answer, unused_team):
        m = re.match(self.challenge.answer_hash, answer, flags=self.re_flags)
        if m:
            return m.group(0) == answer
        return False


class RegexCaseValidator(RegexValidator):
    """Case-insensitive regex match."""

    name = 'Regular Expression (Case Insensitive)'
    re_flags = re.IGNORECASE
