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

from scoreboard.tests import base

from scoreboard import errors
from scoreboard import models
from scoreboard import validators


class ChallengeStub(object):

    def __init__(self, answer, validator='static_pbkdf2'):
        self.answer_hash = answer
        self.validator = validator


class BasicValidatorTest(base.BaseTestCase):

    def testStaticValidator(self):
        chall = ChallengeStub(None)
        validator = validators.GetValidatorForChallenge(chall)
        validator.change_answer('fooabc')
        self.assertTrue(validator.validate_answer('fooabc', None))
        self.assertFalse(validator.validate_answer('abcfoo', None))


class NonceValidatorTest(base.BaseTestCase):

    def setUp(self):
        super(NonceValidatorTest, self).setUp()
        self.cat = models.Category.create('FooCat', 'Foo Cat')
        self.chall = models.Challenge.create(
                'foo', 'bar', 100, '', self.cat.slug, unlocked=True,
                validator='nonce_166432')
        self.validator = validators.GetValidatorForChallenge(self.chall)
        self.validator.change_answer('secret123')
        self.team = models.Team.create('footeam')
        models.commit()

    def testNonceValidator_Basic(self):
        answer = self.validator.make_answer(1)
        self.assertTrue(self.validator.validate_answer(answer, self.team))

    def testNonceValidator_Dupe(self):
        answer = self.validator.make_answer(5)
        self.assertTrue(self.validator.validate_answer(answer, self.team))
        models.commit()
        self.assertTrue(self.validator.validate_answer(answer, self.team))
        self.assertRaises(errors.IntegrityError, models.commit)
