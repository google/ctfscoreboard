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

import hashlib
import hmac

from scoreboard import utils
from scoreboard.validators import base


class PerTeamValidator(base.BaseValidator):
    """Creates a flag that's per-team."""

    name = 'Per-Team'
    flag_gen = True
    per_team = True

    def validate_answer(self, answer, team):
        return utils.compare_digest(
                self.construct_mac(team),
                answer)

    def construct_mac(self, team):
        if not isinstance(team, str):
            if not isinstance(team, int):
                team = team.tid
            team = str(team)
        mac = hmac.new(
                self.challenge.answer_hash,
                team,
                digestmod=hashlib.sha1)
        return mac.hexdigest()
