#!/bin/env python3

from slack_bolt import App
import smtplib
from email.message import EmailMessage
import os
import json
import logging

from typing import Dict, Any

from slack_handlers import handle_message
from env_secrets import EnvVars

# MAIL_NAME_ENV = 'GMAIL_BOT_NAME'
# MAIL_ADDR_ENV = 'GMAIL_BOT_ADDRESS'
# MAIL_PASS_ENV = 'GMAIL_APP_PASSWORD'
# MAIL_DEST_ENV = 'MELIO_INVOICE_EMAIL'
# SLACK_SS_ENV =  'SLACK_SIGNING_SECRET'
# SLACK_BT_ENV =  'SLACK_BOT_TOKEN'


app = App(
    token=EnvVars().get_slack_bot_token(),
    signing_secret=EnvVars().get_slack_signing_secret()
)

logging.basicConfig(level=logging.INFO)



def main():

    # # paths relative to base dir
    # os.chdir('..')

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