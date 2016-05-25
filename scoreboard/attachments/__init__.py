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
Handle attachments via the appropriate backend.

Required API:
    send(models.Attachment): returns a flask response to download attachment
    upload(werkzeug.datastructures.FileStorage): returns attachment ID and path
    delete(models.Attachment): deletes the attachment specified
"""


import urlparse

from scoreboard import app


def get_backend_path():
    """Get backend path for attachments."""
    return app.config.get('ATTACHMENT_BACKEND')


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
