# Copyright 2017 Google Inc. All Rights Reserved.
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

import pbkdf2

from scoreboard import utils
from scoreboard.validators import base


class StaticPBKDF2Validator(base.BaseValidator):
    """PBKDF2-based secrets, everyone gets the same flag."""

    name = 'Static'

    def validate_answer(self, answer, unused_team):
        if not self.challenge.answer_hash:
            return False
        return utils.compare_digest(
                pbkdf2.crypt(answer, self.challenge.answer_hash),
                self.challenge.answer_hash)

    def change_answer(self, answer):
        self.challenge.answer_hash = pbkdf2.crypt(answer)


class CaseStaticPBKDF2Validator(StaticPBKDF2Validator):
    """PBKDF2-based secrets, case insensitive."""

    name = 'Static (Case Insensitive)'

    def validate_answer(self, answer, team):
        if not isinstance(answer, str):
            return False
        return super(CaseStaticPBKDF2Validator, self).validate_answer(
                answer.lower(), team)

    def change_answer(self, answer):
        return super(CaseStaticPBKDF2Validator, self).change_answer(
                answer.lower())
