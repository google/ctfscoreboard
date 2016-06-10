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
Local filesystem backend for attachments.
"""


import hashlib
import os
import os.path
import urlparse

import flask

from scoreboard import main

app = main.get_app()


def attachment_dir(create=False):
    """Return path and optionally create attachment directory."""
    components = urlparse.urlparse(app.config.get('ATTACHMENT_BACKEND'))
    app.config_dir = components.path or components.netloc
    if app.config.get('CWD'):
        target_dir = os.path.normpath(os.path.join(app.config.get('CWD'),
            app.config_dir))
    else:
        target_dir = os.path.abspath(app.config_dir)
    if not os.path.isdir(target_dir):
        if create:
            os.mkdir(target_dir)
        else:
            app.logger.error('Missing or invalid ATTACHMENT_DIR: %s', target_dir)
            flask.abort(500)
    return target_dir


def send(attachment):
    """Send the attachment to the client."""
    return flask.send_from_directory(
        attachment_dir(), attachment.aid,
        mimetype=attachment.content_type,
        attachment_filename=attachment.filename,
        as_attachment=True)


def delete(attachment):
    """Delete the attachment from disk."""
    path = os.path.join(attachment_dir(), attachment.aid)
    os.unlink(path)


def upload(fp):
    """Upload the file attachment to the storage medium."""
    md = hashlib.sha256()
    while True:
        blk = fp.read(2**16)
        if not blk:
            break
        md.update(blk)
    aid = md.hexdigest()
    fp.seek(0, os.SEEK_SET)
    dest_name = os.path.join(attachment_dir(create=True), aid)
    fp.save(dest_name, buffer_size=2**16)
    # TODO: add file:// prefix
    return aid, dest_name
