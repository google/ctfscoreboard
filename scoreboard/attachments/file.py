"""
Local filesystem backend for attachments.
"""


import hashlib
import os
import os.path

import flask

from scoreboard import utils


def send(attachment):
    """Send the attachment to the client."""
    return flask.send_from_directory(
        utils.attachment_dir(), attachment.aid,
        mimetype=attachment.content_type,
        attachment_filename=attachment.filename,
        as_attachment=True)


def delete(attachment):
    """Delete the attachment from disk."""
    path = os.path.join(utils.attachment_dir(), attachment.aid)
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
    dest_name = os.path.join(utils.attachment_dir(create=True), aid)
    fp.save(dest_name, buffer_size=2**16)
    # TODO: add file:// prefix
    return aid, dest_name
