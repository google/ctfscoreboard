"""
Local filesystem backend for attachments.
"""


import hashlib
import os
import os.path
import urlparse

import flask

from scoreboard.app import app
from scoreboard import config


def attachment_dir(create=False):
    """Return path and optionally create attachment directory."""
    components = urlparse.urlparse(config.get('ATTACHMENT_BACKEND'))
    config_dir = components.path or components.netloc
    if config.get('CWD'):
        target_dir = os.path.normpath(os.path.join(config.get('CWD'),
            config_dir))
    else:
        target_dir = os.path.abspath(config_dir)
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
