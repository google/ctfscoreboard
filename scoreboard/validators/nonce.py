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

import base64
import hashlib
import hmac
import struct

from scoreboard import main
from scoreboard import utils
from scoreboard import models

from . import base

app = main.get_app()


class BaseNonceValidator(base.BaseValidator):

    # Bits to use for each of the nonce and authenticator
    NONCE_BITS = 0
    AUTHENTICATOR_BITS = 0
    HASH = hashlib.sha256

    def __init__(self, *args, **kwargs):
        super(BaseNonceValidator, self).__init__(*args, **kwargs)
        if not self.NONCE_BITS or self.NONCE_BITS % 8:
            raise ValueError('NONCE_BITS must be non-0 and a multiple of 8.')
        if not self.AUTHENTICATOR_BITS or self.AUTHENTICATOR_BITS % 8:
            raise ValueError(
                    'AUTHENTICATOR_BITS must be non-0 and a multiple of 8.')

    @staticmethod
    def _decode(buf):
        raise NotImplementedError('Must implement decode.')

    @staticmethod
    def _encode(buf):
        raise NotImplementedError('Must implement encode.')

    def validate_answer(self, answer, team):
        """Validate the nonce-based flag."""
        try:
            decoded_answer = self._decode(answer)
        except TypeError:
            app.logger.error('Invalid padding for answer.')
            return False
        if len(decoded_answer) != (
                self.NONCE_BITS + self.AUTHENTICATOR_BITS) / 8:
            app.logger.error('Invalid length of decoded answer in %s',
                             type(self).__name__)
            return False
        nonce = decoded_answer[:self.NONCE_BITS/8]
        authenticator = decoded_answer[self.NONCE_BITS/8:]
        if not utils.compare_digest(authenticator,
                                    self.compute_authenticator(nonce)):
            app.logger.error('Invalid nonce flag: %s', answer)
            return False
        # At this point, it's a valid flag, but need to check for reuse.
        # We do this by inserting and primary key checks will fail in the
        # commit phase.
        if team:
            models.NonceFlagUsed.create(
                    self.challenge, self.unpack_nonce(nonce),
                    team)
        return True

    def compute_authenticator(self, nonce):
        """Compute the authenticator part for a nonce."""
        mac = hmac.new(
                self.challenge.answer_hash.encode('utf-8'),
                nonce,
                digestmod=self.HASH).digest()
        return mac[:self.AUTHENTICATOR_BITS/8]

    def make_answer(self, nonce):
        """Compute the whole answer for a nonce."""
        if isinstance(nonce, int):
            nonce = struct.pack('>Q', nonce)
            nonce = nonce[8 - (self.NONCE_BITS / 8):]
        if len(nonce) != self.NONCE_BITS / 8:
            raise ValueError('nonce is wrong length!')
        return self._encode(nonce + self.compute_authenticator(nonce))

    @classmethod
    def unpack_nonce(cls, nonce):
        pad = '\x00' * (8 - cls.NONCE_BITS / 8)
        return struct.unpack('>Q', pad + nonce)[0]


class Base32Validator(BaseNonceValidator):

    def __init__(self, *args, **kwargs):
        if (self.NONCE_BITS + self.AUTHENTICATOR_BITS) % 5 != 0:
            raise ValueError('Length must be a mulitple of 5 bits.')
        super(Base32Validator, self).__init__(*args, **kwargs)

    @staticmethod
    def _encode(buf):
        return base64.b32encode(buf)

    @staticmethod
    def _decode(buf):
        if isinstance(buf, unicode):
            buf = buf.encode('utf-8')
        return base64.b32decode(buf, casefold=True, map01='I')


class Nonce_16_64_Base32_Validator(Base32Validator):

    name = 'Nonce: 16 bits, 64 bit validator, Base32 encoded'
    NONCE_BITS = 16
    AUTHENTICATOR_BITS = 64


class Nonce_32_88_Base32_Validator(Base32Validator):

    name = 'Nonce: 32 bits, 88 bit validator, Base32 encoded'
    NONCE_BITS = 32
    AUTHENTICATOR_BITS = 88
