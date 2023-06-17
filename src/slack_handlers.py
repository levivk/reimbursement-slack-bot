
from typing import Dict, Any
from slack_bolt.context.say.say import Say
import logging
import json

logger = logging.getLogger(__name__)

def handle_message(message: Dict[str, Any], say: Say):
    """
    pass to App.event to handle slack messages
    """
    if is_reimbursement_channel(message):
        handle_reimbursement_post(message, say)


def handle_reimbursement_post(message: Dict[str, Any], say: Say):
    """
    Handle a post to the reimbursement channel
    """
    logger.info(message)
    if not is_reimbursement_channel(message):
        return

    # If it has an attachment jpg or png, reply with invoice number and email attachment
    if "files" in message:
        for attachment in message["files"]:
            if attachment['mimetype'] not in ['image/jpg', 'image/png']:
                continue

            #TODO: inc receipt #
            say('receipt #', thread_ts=message['ts'])
            #TODO: email attachment
    
    # If it is top level comment without a receipt, reply asking for one
    elif "thread_ts" not in message:
        say('Please post the receipt', thread_ts=message['ts'])


    print('\nmessage:\n', json.dumps(message, indent=4))
    # say('Fight me', username='Reimbursement bot')


# TODO: get list of channels and get chan ID from there, rather than magic number
def is_reimbursement_channel(message: Dict[str, Any]) -> bool:
    """
    True if the message is from the reimbursement channel
    """
    try:
        chan = message["channel"]
    except KeyError:
        return False
    
    return chan == "C05CF7LFU5U"






