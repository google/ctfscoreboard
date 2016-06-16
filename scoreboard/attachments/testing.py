# Copyright 2016 Google Inc. All Rights Reserved.
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


"""
Volatile filesystem backend for attachments.
"""


import hashlib
import os
import os.path
import urlparse

import flask
import StringIO

from scoreboard import main

app = main.get_app()

files = {}

def send(attachment):
    """Send the attachment to the client."""
    return flask.send_file(files[attachment.aid],
                           attachment_filename="testing.txt",
                           as_attachment=True)


def delete(attachment):
    """Delete the attachment from disk."""
    del files[attachment.aid]


def upload(fp):
    """Upload the file attachment to the storage medium."""
    md = hashlib.sha256()
    ret = StringIO.StringIO()
    while True:
        blk = fp.read(2**16)
        if not blk:
            break
        md.update(blk)
        ret.write(blk)
    aid = md.hexdigest()
    ret.seek(0)
    files[aid] = ret
    return aid, ('test://%s' % aid)
