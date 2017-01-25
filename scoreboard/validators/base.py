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


class BaseValidator(object):

    # Can we generate these flags?
    flag_gen = False
    # Is this flag per team?
    per_team = False

    def __init__(self, challenge):
        self.challenge = challenge

    def validate_answer(self, answer, team):
        """Validate the answer for the team."""
        raise NotImplementedError(
                '%s does not implement validate_answer.' %
                type(self).__name__)

    def change_answer(self, answer):
        """Change the answer for the challenge."""
        self.challenge.answer_hash = answer
