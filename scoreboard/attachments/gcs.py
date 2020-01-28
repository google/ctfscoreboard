# Copyright 2016 Google LLC. All Rights Reserved.
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
Attachments on Google Cloud Storage.
"""


import hashlib
import os
try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse
try:
    from io import BytesIO
except ImportError:
    try:
        import cStringIO.StringIO as BytesIO
    except ImportError:
        import StringIO.StringIO as BytesIO


import flask

from google.cloud import storage
from google.cloud import exceptions

from scoreboard import main

app = main.get_app()


def get_bucket(path=None):
    path = path or app.config.get('ATTACHMENT_BACKEND')
    url = urlparse.urlparse(path)
    return url.netloc


def send(attachment):
    """Send to download URI."""
    try:
        client = storage.Client()
        bucket = client.bucket(get_bucket())
        buf = BytesIO()
        blob = bucket.get_blob(attachment.aid)
        if not blob:
            return flask.abort(404)
        blob.download_to_file(buf)
        buf.seek(0)
        return flask.send_file(
            buf,
            mimetype=attachment.content_type,
            attachment_filename=attachment.filename,
            add_etags=False, as_attachment=True)
    except exceptions.NotFound:
        return flask.abort(404)


def delete(attachment):
    """Delete from GCS Bucket."""
    try:
        client = storage.Client()
        bucket = client.bucket(get_bucket())
        bucket.delete_blob(attachment.aid)
    except exceptions.NotFound:
        return flask.abort(404)


def upload(fp):
    """Upload the attachment."""
    md = hashlib.sha256()
    while True:
        blk = fp.read(2**16)
        if not blk:
            break
        md.update(blk)
    fp.seek(0, os.SEEK_SET)
    aid = md.hexdigest()
    client = storage.Client()
    bucket = client.bucket(get_bucket())
    blob = bucket.blob(aid)
    blob.upload_from_file(fp)
    path = 'gcs://{}/{}'.format(get_bucket(), aid)
    return aid, path
