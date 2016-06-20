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


# Demo config.py, please configure your own
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/scoreboard.db'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SECRET_KEY = 'CHANGEME CHANGEME CHANGEME'
# Set TEAM_SECRET_KEY to a unique value so that you can rotate session
# secrets (SECRET_KEY) without affecting team invite codes.
TEAM_SECRET_KEY = SECRET_KEY
TITLE = 'CTF Scoreboard Dev'
TEAMS = True
ATTACHMENT_BACKEND = 'file:///tmp/attachments'
LOGIN_METHOD = 'local'
