# Copyright 2016 David Tomaschik <david@systemoverlord.com>
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


import logging

import flask


class Formatter(logging.Formatter):
    """Custom formatter to handle application logging.
    
    This formatter adds a "client" attribute that will log the user and client
    information.
    """

    def format(self, record):
        if flask.request:
            user = repr(flask.g.user) if flask.g.user else "-"
            record.client = "[{}/{}]".format(flask.request.remote_addr, user)
        else:
            record.client = ""
        return super(Formatter, self).format(record)
