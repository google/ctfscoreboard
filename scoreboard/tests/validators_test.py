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


class StaticValidatorTest(base.BaseTestCase):

    def testStaticValidator(self):
        chall = ChallengeStub(None)
        validator = validators.GetValidatorForChallenge(chall)
        self.assertFalse(validator.validate_answer('fooabc', None))
        validator.change_answer('fooabc')
        self.assertTrue(validator.validate_answer('fooabc', None))
        self.assertFalse(validator.validate_answer('abcfoo', None))


class CaseStaticValidatorTest(base.BaseTestCase):

    def testCaseStaticValidator(self):
        chall = ChallengeStub(None, validator='static_pbkdf2_ci')
        validator = validators.GetValidatorForChallenge(chall)
        self.assertFalse(validator.validate_answer('foo', None))
        validator.change_answer('FooBar')
        for test in ('FooBar', 'foobar', 'FOOBAR', 'fooBAR'):
            self.assertTrue(
                    validator.validate_answer(test, None),
                    msg='Case failed: {}'.format(test))
        for test in ('barfoo', 'bar', 'foo', None):
            self.assertFalse(
                    validator.validate_answer(test, None),
                    msg='Case failed: {}'.format(test))


class RegexValidatorTest(base.BaseTestCase):

    def makeValidator(self, regex):
        """Construct a validator."""
        chall = ChallengeStub(regex, validator='regex')
        return validators.GetValidatorForChallenge(chall)

    def testRegexWorks(self):
        v = self.makeValidator('[abc]+')
        self.assertTrue(v.validate_answer('aaa', None))
        self.assertTrue(v.validate_answer('abc', None))
        self.assertFalse(v.validate_answer('ddd', None))
        self.assertFalse(v.validate_answer('aaad', None))
        self.assertFalse(v.validate_answer('AAA', None))

    def testRegexChangeWorks(self):
        v = self.makeValidator('[abc]+')
        self.assertTrue(v.validate_answer('a', None))
        self.assertFalse(v.validate_answer('foo', None))
        v.change_answer('fo+')
        self.assertTrue(v.validate_answer('foo', None))
        self.assertFalse(v.validate_answer('a', None))


class RegexCaseValidatorTest(base.BaseTestCase):

    def makeValidator(self, regex):
        """Construct a validator."""
        chall = ChallengeStub(regex, validator='regex_ci')
        return validators.GetValidatorForChallenge(chall)

    def testRegexWorks(self):
        v = self.makeValidator('[abc]+')
        self.assertTrue(v.validate_answer('aaa', None))
        self.assertTrue(v.validate_answer('abc', None))
        self.assertFalse(v.validate_answer('ddd', None))
        self.assertFalse(v.validate_answer('aaad', None))
        self.assertTrue(v.validate_answer('AAA', None))

    def testRegexChangeWorks(self):
        v = self.makeValidator('[abc]+')
        self.assertTrue(v.validate_answer('a', None))
        self.assertFalse(v.validate_answer('foo', None))
        v.change_answer('fo+')
        self.assertTrue(v.validate_answer('Foo', None))
        self.assertFalse(v.validate_answer('a', None))


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
