"""
Attachments on Google Cloud Storage.
"""


import hashlib
import os
import urlparse

import flask

import cloudstorage as gcs

from scoreboard.app import app


def get_bucket(path=None):
    path = path or app.config.get('ATTACHMENT_BACKEND', '')
    url = urlparse.urlparse(path)
    return url.netloc


def make_path(aid):
    return '/%s/%s' % (get_bucket(), aid)


def send(attachment):
    """Send to download URI."""
    path = make_path(attachment.aid)
    try:
        fp = gcs.open(path)
        return flask.send_file(fp,
            mimetype=attachment.content_type,
            attachment_filename=attachment.filename,
            add_etags=False, as_attachment=True)
    except gcs.NotFoundError:
        return flask.abort(404)


def delete(attachment):
    """Delete from GCS Bucket."""
    path = make_path(attachment.aid)
    try:
        gcs.delete(path)
    except gcs.NotFoundError:
        pass


def upload(fp):
    """Upload the attachment."""
    md = hashlib.sha256()
    while True:
        blk = fp.read(2**16)
        if not blk:
            break
        md.update(blk)
    aid = md.hexdigest()
    path = make_path(aid)
    gcsfp = gcs.open(path, "w", content_type=fp.mimetype)
    while True:
        blk = fp.read(2**16)
        if not blk:
            break
        gcsfp.write(blk)
    gcsfp.close()
    return aid, path
