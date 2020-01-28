# Copyright 2018 Google LLC. All Rights Reserved.
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

from email.mime import text
import email.utils
import smtplib
import socket

from scoreboard import main

app = main.get_app()


class MailFailure(Exception):
    """Inability to send mail."""
    pass


def send(message, subject, to, to_name=None, sender=None, sender_name=None):
    """Send an email."""
    sender = sender or app.config.get('MAIL_FROM')
    sender_name = sender_name or app.config.get('MAIL_FROM_NAME')
    _send_smtp(message, subject, to, to_name, sender, sender_name)


def _send_smtp(message, subject, to, to_name, sender, sender_name):
    """SMTP implementation of sending email."""
    host = app.config.get('MAIL_HOST')

    if not host:
        raise MailFailure('SMTP Server Not Configured')

    try:
        server = smtplib.SMTP(host)
    except (smtplib.SMTPConnectError, socket.error) as ex:
        app.logger.error('Unable to send mail: %s', str(ex))
        raise MailFailure('Error connecting to SMTP server.')

    msg = text.MIMEText(message)
    msg['Subject'] = subject
    msg['To'] = email.utils.formataddr((to_name, to))
    msg['From'] = email.utils.formataddr((sender_name, sender))

    try:
        if app.debug:
            server.set_debuglevel(True)
        server.sendmail(sender, [to], msg.as_string())
    except (smtplib.SMTPException, socket.error) as ex:
        app.logger.error('Unable to send mail: %s', str(ex))
        raise MailFailure('Error sending mail to SMTP server.')
    finally:
        try:
            server.quit()
        except smtplib.SMTPException:
            pass
