"""
Handle attachments via the appropriate backend.

Required API:
    send(models.Attachment): returns a flask response to download attachment
    upload(werkzeug.datastructures.FileStorage): returns attachment ID and path
    delete(models.Attachment): deletes the attachment specified
"""


import urlparse

from scoreboard.app import app


def get_backend_path():
    """Get backend path for attachments."""
    return app.config.get('ATTACHMENT_BACKEND', 'file://attachments')


def get_backend_type():
    """Determine type of backend."""
    backend = get_backend_path()
    return urlparse.urlparse(backend).scheme


_backend_type = get_backend_type()
if _backend_type == "file":
    from scoreboard.attachments.file import *
elif _backend_type == "gcs":
    from scoreboard.attachments.gcs import * 
else:
    raise ImportError('Unhandled attachment backend %s' % _backend_type)
