#!/bin/env python3

from slack_bolt import App
import smtplib
from email.message import EmailMessage
import os
import json
import logging

from typing import Dict, Any

from slack_handlers import handle_message

MAIL_NAME_ENV = 'GMAIL_BOT_NAME'
MAIL_ADDR_ENV = 'GMAIL_BOT_ADDRESS'
MAIL_PASS_ENV = 'GMAIL_APP_PASSWORD'
MAIL_DEST_ENV = 'MELIO_INVOICE_EMAIL'
SLACK_SS_ENV =  'SLACK_SIGNING_SECRET'
SLACK_BT_ENV =  'SLACK_BOT_TOKEN'


app = App(
    token=os.environ.get(SLACK_BT_ENV),
    signing_secret=os.environ.get(SLACK_SS_ENV)
)

logging.basicConfig(level=logging.INFO)



def main():

    mail_name = os.environ.get(MAIL_NAME_ENV)
    mail_addr = os.environ.get(MAIL_ADDR_ENV)
    mail_password = os.environ.get(MAIL_PASS_ENV)
    mail_dest = os.environ.get(MAIL_DEST_ENV)
    slack_ss = os.environ.get(SLACK_SS_ENV)
    slack_bt = os.environ.get(SLACK_BT_ENV)

    # PYRIGHT doesn't consider "if None in [...]" to be a valid type check
    if not mail_name or not mail_addr or not mail_password or not mail_dest or not slack_ss or not slack_bt:
        raise ValueError(f"Must define evironment variables: {MAIL_NAME_ENV}, {MAIL_ADDR_ENV}, {MAIL_PASS_ENV}, {MAIL_DEST_ENV}, {SLACK_SS_ENV}, {SLACK_BT_ENV}")

    # Create slack app

    # add listeners
    app.event({'type':'message'})(handle_message)
    # app.event({'type':'message'})(handle_reimbursement_post)

    app.start(port=3000)



    # filename = 'faker1.jpg'

    # msg = EmailMessage()
    # msg["From"] = f'{mail_name} <{mail_addr}>'
    # msg["To"] = mail_dest
    # msg["Subject"] = filename
    # msg.set_content("This is invoice")

    # with open(filename, 'br') as f:
    #     filedata = f.read()
    # msg.add_attachment(filedata, 'image', 'jpeg', filename=filename)

    # server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    # server.login(mail_addr, mail_password)
    # server.send_message(msg)
    # server.quit()

if __name__ == '__main__':
    main()