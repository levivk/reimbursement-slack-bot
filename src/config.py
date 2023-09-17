"""Module to handle environment variables"""

import os
from enum import StrEnum


class ConfigVars(StrEnum):
    MAIL_NAME = 'GMAIL_BOT_NAME'
    MAIL_ADDR = 'GMAIL_BOT_ADDRESS'
    MAIL_PASS = 'GMAIL_APP_PASSWORD'
    MAIL_DEST = 'MELIO_INVOICE_EMAIL'
    SLACK_SS = 'SLACK_SIGNING_SECRET'
    SLACK_BT = 'SLACK_BOT_TOKEN'


def check_env_vars():
    '''Check that the necessary environment variables are set'''
    missing = []
    for k in ConfigVars:
        v = os.environ.get(k)
        if v is None:
            missing.append(k)
    # Print out what is missing
    if missing:
        m = '\n'.join(missing)
        raise ValueError(
            f'The following environment variables need to be set:\n{m}'
        )


def get_mail_bot_name():
    return os.environ.get(ConfigVars.MAIL_NAME)


def get_mail_bot_address():
    return os.environ.get(ConfigVars.MAIL_ADDR)


def get_mail_bot_password():
    return os.environ.get(ConfigVars.MAIL_PASS)


def get_destination_email():
    return os.environ.get(ConfigVars.MAIL_DEST)


def get_slack_signing_secret():
    return os.environ.get(ConfigVars.SLACK_SS)


def get_slack_bot_token():
    return os.environ.get(ConfigVars.SLACK_BT)


def test():
    check_env_vars()
    print(f'mail name: {get_mail_bot_name()}')
    print(f'mail addr: {get_mail_bot_address()}')
    print(f'mail pass: {get_mail_bot_password()}')
    print(f'mail dest: {get_destination_email()}')
    print(f'slack ss: {get_slack_signing_secret()}')
    print(f'slack bt: {get_slack_bot_token()}')


if __name__ == '__main__':
    test()
