# Copyright 2014 David Tomaschik <david@systemoverlord.com>
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

import flask
import json

from app import app
import csrfutil
import models
import os
import utils


@app.route('/admin/backup/challenges')
@utils.admin_required
def admin_challenge_backup():
    # TODO: remove if not needed
    categories = {}
    for cat in models.Category.query.all():
        challenges = []
        for q in cat.challenges:
            hints = []
            for h in q.hints:
                hints.append({
                    'hint': h.hint,
                    'cost': h.cost,
                })
            challenges.append({
                'category': cat.cid,
                'name': q.name,
                'description': q.description,
                'points': q.points,
                'answer_hash': q.answer_hash,
                'hints': hints,
            })
        categories[cat.cid] = {
            'name': cat.name,
            'description': cat.description,
            'challenges': challenges,
        }
    response = flask.jsonify(categories=categories)
    response.headers[
        'Content-Disposition'] = 'attachment; filename=challenges.json'
    return response


@app.route('/admin/backup/challenges/restore', methods=['POST'])
@utils.admin_required
@csrfutil.csrf_protect
def admin_challenge_restore():
    # TODO: angularify
    jsfile = flask.request.files.get('restorefile')
    if not jsfile:
        flask.flash('No JSON file was sent.', 'warning')
        return
    try:
        data = json.load(jsfile)
    except ValueError:
        flask.flash('Invalid JSON!', 'danger')
        return

    if flask.request.form.get('replace') == 'True':
        models.Hint.query.delete()
        models.Challenge.query.delete()
        models.Category.query.delete()

    cats = {}
    for catid, cat in data['categories'].iteritems():
        newcat = models.Category()
        for f in ('name', 'description'):
            setattr(newcat, f, cat[f])
        models.db.session.add(newcat)
        cats[int(catid)] = newcat

        for challenge in cat['challenges']:
            newchall = models.Challenge()
            for f in ('name', 'description', 'points', 'answer_hash'):
                setattr(newchall, f, challenge[f])
            newchall.category = newcat
            models.db.session.add(newchall)
            for h in challenge.get('hints', []):
                hint = models.Hint()
                hint.challenge = newchall
                hint.hint = h['hint']
                hint.cost = int(h['cost'])
                models.db.session.add(hint)

    models.commit()
    return flask.redirect('/admin/categories')


@app.route('/attachment/<filename>')
@utils.login_required
def download(filename):
    attachment = models.Attachment.query.get_or_404(filename)
    if not attachment.challenge.unlocked:
        flask.abort(404)

    return flask.send_from_directory(
        utils.attachment_dir(), filename,
        mimetype=attachment.content_type,
        attachment_filename=attachment.filename,
        as_attachment=True)
