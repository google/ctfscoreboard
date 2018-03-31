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


# Production appengine config
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://scoreboard:Wo3Fun8iceji@/scoreboard?unix_socket=/cloudsql/bsides-sf-ctf-2018-197221:us-central1:scoreboard'
SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/scoreboard.db'
SQLALCHEMY_TRACK_MODIFICATIONS = True
SECRET_KEY = 'uelaemoy5eineipah0theetohb2Oogoh'
# Set TEAM_SECRET_KEY to a unique value so that you can rotate session
# secrets (SECRET_KEY) without affecting team invite codes.
TEAM_SECRET_KEY = 'UshohmahphohzeeCh3sho3eiP0ahfuth'
TITLE = 'BSidesSF 2018 CTF'
TEAMS = True
#ATTACHMENT_BACKEND = 'gcs://bsidessf-scoreboard-objects'
LOGIN_METHOD = 'local'
SESSION_COOKIE_SECURE = False
PROOF_OF_WORK_BITS = 12
TAGS_ONLY = True
#INVITE_KEY = 'I Know Matir'
#GAME_TIME = ('2018-04-15 09:00:00 -0700', '2018-04-16 16:00:00 -0700')
