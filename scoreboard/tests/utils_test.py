# Copyright 2018 Google LLC. All Rights Reserved.
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

from scoreboard import utils


class NormalizeInputTest(base.BaseTestCase):

    def testNormalizeInput(self):
        ni = utils.normalize_input  # Shorthand
        self.assertEqual(ni("hello"), "hello")
        self.assertEqual(ni("Hello World"), "Hello World")
        self.assertEqual(ni(" foo "), "foo")


class ProofOfWorkTest(base.BaseTestCase):

    def testValidateProofOfWork_Succeeds(self):
        val = "foo"
        key = "N77manQK9CvjvPRXB8U7ftJxys1d36xVfcBkGvM-jqM"
        nbits = 12
        self.assertTrue(utils.validate_proof_of_work(val, key, nbits))

    def testValidateProofOfWork_SucceedsUnicode(self):
        val = u"foo"
        key = u"N77manQK9CvjvPRXB8U7ftJxys1d36xVfcBkGvM-jqM"
        nbits = 12
        self.assertTrue(utils.validate_proof_of_work(val, key, nbits))

    def testValidateProofOfWork_FailsWrongVal(self):
        val = "bar"
        key = "N77manQK9CvjvPRXB8U7ftJxys1d36xVfcBkGvM-jqM"
        nbits = 12
        self.assertFalse(utils.validate_proof_of_work(val, key, nbits))

    def testValidateProofOfWork_FailsWrongKey(self):
        val = "foo"
        key = "N77manQK9CvjvPRXB8U7ftJxys1d36xVfcBkGvM-jq"
        nbits = 12
        self.assertFalse(utils.validate_proof_of_work(val, key, nbits))

    def testValidateProofOfWork_FailsMoreBits(self):
        val = "foo"
        key = "N77manQK9CvjvPRXB8U7ftJxys1d36xVfcBkGvM-jq"
        nbits = 16
        self.assertFalse(utils.validate_proof_of_work(val, key, nbits))

    def testValidateProofOfWork_FailsInvalidBase64(self):
        val = "foo"
        key = "!!"
        nbits = 12
        self.assertFalse(utils.validate_proof_of_work(val, key, nbits))
