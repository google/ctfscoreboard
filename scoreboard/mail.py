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
import mailjet_rest

from scoreboard import main

app = main.get_app()


class MailFailure(Exception):
    """Inability to send mail."""
    pass


def send(message, subject, to, to_name=None, sender=None, sender_name=None):
    """Send an email."""
    sender = sender or app.config.get('MAIL_FROM')
    sender_name = sender_name or app.config.get('MAIL_FROM_NAME') or ''
    mail_provider = app.config.get('MAIL_PROVIDER')
    if mail_provider is None:
        app.logger.error('No MAIL_PROVIDER configured!')
        raise MailFailure('No MAIL_PROVIDER configured!')
    elif mail_provider == 'smtp':
        _send_smtp(message, subject, to, to_name, sender, sender_name)
    elif mail_provider == 'mailjet':
        _send_mailjet(message, subject, to, to_name, sender, sender_name)
    else:
        app.logger.error('Invalid MAIL_PROVIDER configured!')
        raise MailFailure('Invalid MAIL_PROVIDER configured!')


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


def _send_mailjet(message, subject, to, to_name, sender, sender_name):
    """Mailjet implementation of sending email."""
    api_key = app.config.get('MJ_APIKEY_PUBLIC')
    api_secret = app.config.get('MJ_APIKEY_PRIVATE')
    if not api_key or not api_secret:
        app.logger.error('Missing MJ_APIKEY_PUBLIC/MJ_APIKEY_PRIVATE!')
        return
    # Note the data structures we use are api v3.1
    client = mailjet_rest.Client(
            auth=(api_key, api_secret),
            api_url='https://api.mailjet.com/',
            version='v3.1')
    from_obj = {
            "Email": sender,
    }
    if sender_name:
        from_obj["Name"] = sender_name
    to_obj = [{
        "Email": to,
    }]
    if to_name:
        to_obj[0]["Name"] = to_name
    message = {
            "From": from_obj,
            "To": to_obj,
            "Subject": subject,
            "TextPart": message,
    }
    result = client.send.create(data={'Messages': [message]})
    if result.status_code != 200:
        app.logger.error(
                'Error sending via mailjet: (%d) %r',
                result.status_code, result.text)
        raise MailFailure('Error sending via mailjet!')
    try:
        j = result.json()
    except Exception:
        app.logger.error('Error sending via mailjet: %r', result.text)
        raise MailFailure('Error sending via mailjet!')
    if j['Messages'][0]['Status'] != 'success':
        app.logger.error('Error sending via mailjet: %r', j)
        raise MailFailure('Error sending via mailjet!')
