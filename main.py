#!/bin/env python3

import smtplib
from email.message import EmailMessage
import os

MAIL_ADDR_ENV = 'GMAIL_BOT_ADDRESS'
MAIL_PASS_ENV = 'GMAIL_APP_PASSWORD'

mail_user = os.environ.get(MAIL_ADDR_ENV)
mail_password = os.environ.get(MAIL_PASS_ENV)

if(mail_user == None or mail_password == None):
    raise ValueError(f"Must define evironment variables: {MAIL_ADDR_ENV} and {MAIL_PASS_ENV}")

msg = EmailMessage()
msg["From"] = mail_user
msg["To"] = 'redacted'
msg["Subject"] = "I am snek"
msg.set_content("This is content baby!")

with open('content.jpg', 'br') as f:
    data = f.read()
msg.add_attachment(data, 'picture', 'jpeg', filename='content.jpg')

server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
server.login(mail_user, mail_password)
server.send_message(msg)
server.quit()