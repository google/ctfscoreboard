# Copyright 2017 Google LLC. All Rights Reserved.
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


from . import static_argon2
from . import per_team
from . import nonce
from . import regex

_Validators = {
        'static_argon2': static_argon2.StaticArgon2Validator,
        'static_argon2_ci': static_argon2.CaseStaticArgon2Validator,
        'per_team': per_team.PerTeamValidator,
        'nonce_166432': nonce.Nonce_16_64_Base32_Validator,
        'nonce_245632': nonce.Nonce_24_56_Base32_Validator,
        'nonce_328832': nonce.Nonce_32_88_Base32_Validator,
        'regex': regex.RegexValidator,
        'regex_ci': regex.RegexCaseValidator,
        }


def GetDefaultValidator():
    return 'static_argon2'


def GetValidatorForChallenge(challenge):
    cls = _Validators[challenge.validator]
    return cls(challenge)


def ValidatorNames():
    return {k: getattr(v, 'name', k) for k, v in _Validators.items()}


def ValidatorMeta():
    meta = {}
    for k, v in _Validators.items():
        meta[k] = {
                'name': v.name,
                'per_team': v.per_team,
                'flag_gen': v.flag_gen,
                }
    return meta


def IsValidator(name):
    return name in _Validators


__all__ = [GetValidatorForChallenge, ValidatorNames]
