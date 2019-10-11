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

import sys


def main(argv):
    if len(argv) > 1 and argv[1] == 'runtests':
        from scoreboard.tests import base
        if len(argv) > 2:
            if not base.run_all_tests(argv[2]):
                sys.exit(1)
            return
        if not base.run_all_tests():
            sys.exit(1)
        return

    # This needs to only be imported when not testing
    from scoreboard import wsgi
    from scoreboard import models
    if 'createdb' in argv:
        models.db.create_all()
    elif 'createdata' in argv:
        from scoreboard.tests import data
        models.db.create_all()
        data.create_all()
    elif 'shell' in argv:
        try:
            import IPython
            run_shell = IPython.embed
        except ImportError:
            import readline  # noqa: F401
            import code
            run_shell = code.InteractiveConsole().interact
        run_shell()
    else:
        wsgi.app.run(
                host='0.0.0.0', debug=True,
                port=wsgi.app.config.get('PORT', 9999))


if __name__ == '__main__':
    main(sys.argv)
