"""Module to handle environment variables"""

from typing import NamedTuple
import os


class EnvVarsTup(NamedTuple):
    MAIL_NAME: str = 'GMAIL_BOT_NAME'
    MAIL_ADDR: str = 'GMAIL_BOT_ADDRESS'
    MAIL_PASS: str = 'GMAIL_APP_PASSWORD'
    MAIL_DEST: str = 'MELIO_INVOICE_EMAIL'
    SLACK_SS: str = 'SLACK_SIGNING_SECRET'
    SLACK_BT: str = 'SLACK_BOT_TOKEN'


class EnvVars:
    """A singleton class that stores secrets from environment variables"""

    env_names = EnvVarsTup()
    env_values: EnvVarsTup

    # Singleton
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(EnvVars, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        # Get values
        d = dict()
        for n in self.env_names._fields:
            env_name = getattr(self.env_names, n)
            d[n] = os.environ.get(getattr(self.env_names, n))
            if not d[n]:
                raise ValueError(
                    f'Environment varaible {env_name} not set! Must set evironment variables:'
                    f'{" ".join(self.env_names)}')
        self.env_values = EnvVarsTup(**d)

    def get_mail_bot_name(self):
        return self.env_values.MAIL_NAME

    def get_mail_bot_address(self):
        return self.env_values.MAIL_ADDR

    def get_mail_bot_password(self):
        return self.env_values.MAIL_PASS

    def get_destination_email(self):
        return self.env_values.MAIL_DEST

    def get_slack_signing_secret(self):
        return self.env_values.SLACK_SS

    def get_slack_bot_token(self):
        return self.env_values.SLACK_BT


# def assert_environment_variables():
#     names = EnvVarNames()
#     for n in names:
#         val = os.environ.get(n)
#         if not val:
#             raise ValueError(f"Must define evironment variables: {' '.join(names)}")
