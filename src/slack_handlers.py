
from typing import Dict, Any
from slack_bolt.context.say.say import Say
from slack_sdk import WebClient
import logging
import json
from datetime import datetime
from pathlib import Path
from storage import PersistentTable
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import smtplib
from email.message import EmailMessage
from env_secrets import EnvVars


RECEIPT_MOD_MARGIN_HEIGHT = 600
RECEIPT_RESIZE_WIDTH = 3000
BOT_DISPLAY_NAME = 'Reimbursement Bot'
BOT_ICON = ':money_with_wings:'

logger = logging.getLogger(__name__)


def convert_date(s: str) -> None | datetime:
    if s == '':
        return None
    else:
        return datetime.fromisoformat(s)


converters = dict(
    invoice=int,
    slack_ts=None,
    date_requested=convert_date,
    date_payment_sent=convert_date,

)
csv_path = (Path(__file__).parent / "../data/reimbursements.csv").resolve()
# with open(csv_path, 'r') as f:
#     print(f.read())
receipt_table = PersistentTable(
    str(csv_path),
    fieldnames=list(converters.keys()),
    converters=converters
)


def handle_message(message: Dict[str, Any], say: Say, client: WebClient, body: Dict[str, Any]):
    """
    pass this function to App.event to handle slack messages
    """
    if is_reimbursement_channel(message):
        handle_reimbursement_post(message, say, client, body)
    elif is_im(message):
        handle_im(message, say)
    else:
        print(json.dumps(message, indent=4))
        logger.info(f'Unhandled message from user {message["user"]} \
            on channel {message["channel"]}')


def handle_reimbursement_post(message: Dict[str, Any], say: Say,
                              client: WebClient, body: Dict[str, Any]):
    """
    Handle a post to the reimbursement channel
    """
    logger.info(f'Received reimbursement post from user {message["user"]}')

    # If it has an attachment jpg or png, reply with invoice number and email attachment
    if "files" in message:
        logger.info('Post has attachment(s)')
        for attachment in message["files"]:
            if attachment['mimetype'] not in ['image/jpg', 'image/jpeg', 'image/png']:
                continue

            # increment receipt number
            try:
                receipt_num: int = receipt_table[-1]['invoice'] + 1
            except IndexError:
                receipt_num = 1

            # Extract message text
            try:
                message_text = message['text']
            except KeyError:
                message_text = 'No message text'

            # Get user's name
            resp = client.users_info(user=message['user'])
            user_dict = resp['user']
            if user_dict is None:
                uname = 'Error getting user'
            elif user_dict['real_name'] is not None:
                uname = user_dict['real_name']
            else:
                uname = user_dict['name']

            # handle the receipt
            process_receipt(
                download_url=attachment['url_private'],
                receipt_number=receipt_num,
                uploader_name=uname,
                message=message_text
            )

            # Respond with receipt number
            say(f'Thank you, your reimbursement is being processed. Receipt #{receipt_num:05}.',
                thread_ts=message['ts'], username=BOT_DISPLAY_NAME, icon_emoji=BOT_ICON)
            logger.info(f'Processing receipt #{receipt_num:05}')

            receipt_table.append(invoice=receipt_num, slack_ts=message['ts'],
                                 date_requested=datetime.now(), date_payment_sent=None)

    # Otherwise, if it is top level comment, reply asking for a receipt
    elif "thread_ts" not in message:
        say('Please post the receipt',
            thread_ts=message['ts'], username=BOT_DISPLAY_NAME, icon_emoji=BOT_ICON)

    print('\body:\n', json.dumps(body, indent=4))


def handle_im(message: Dict[str, Any], say: Say):
    say('Fight me')


# TODO: get list of channels and get chan ID from there, rather than magic number
def is_reimbursement_channel(message: Dict[str, Any]) -> bool:
    """
    True if the message is from the reimbursement channel
    """
    try:
        chan = message["channel"]
    except KeyError:
        return False

    # return chan == "C05CF7LFU5U"
    return chan == "C9NG0FSG4"


def is_im(message: Dict[str, Any]) -> bool:
    return message['channel_type'] == 'im'


def process_receipt(
        download_url: str,
        uploader_name: str,
        receipt_number: int,
        message: str,
        show: bool = False
):
    """Download the picture, add a text header to the picture, and email the picture to the
    payment processor"""

    # Download file
    slack_bot_token = EnvVars().get_slack_bot_token()
    r = requests.get(download_url, headers={'Authorization': f'Bearer {slack_bot_token}'})
    r.raise_for_status()
    file_data = r.content

    # Create image object and scale
    with BytesIO(file_data) as bio:
        im = Image.open(bio)
        # Scale image to constant width
        width, height = im.size
        scale_height = int(height * RECEIPT_RESIZE_WIDTH / width)
        im_scaled = im.convert('RGB').resize((RECEIPT_RESIZE_WIDTH, scale_height))
        im.close()

    # Create header text
    header_img = Image.new(im_scaled.mode, (RECEIPT_RESIZE_WIDTH, RECEIPT_RESIZE_WIDTH),
                           (255, 255, 255))
    font = ImageFont.truetype('LiberationSans-Regular.ttf', size=170)
    imdr = ImageDraw.Draw(header_img)
    text_1 = 'Pay to: ' + uploader_name
    text_2 = f'Receipt #{receipt_number:05}'
    text_3 = f'Date requested: {datetime.now().date()}'
    text_4 = get_wrapped_text('Message: ' + message, font, RECEIPT_RESIZE_WIDTH)
    all_text = '\n'.join([text_1, text_2, text_3, text_4])
    text_height = imdr.textbbox(xy=(20, 0), text=all_text, font=font)[3]
    text_height += 20
    if text_height > RECEIPT_RESIZE_WIDTH:
        # resize
        temp_im = header_img.resize((RECEIPT_RESIZE_WIDTH, text_height))
        header_img.close()
        header_img = temp_im
        imdr = ImageDraw.Draw(header_img)
    imdr.text(xy=(20, 0), text=all_text, fill=(0, 0, 0), font=font)

    # Resize to text
    header_img_crop = header_img.crop((0, 0, RECEIPT_RESIZE_WIDTH, text_height))
    header_img.close()

    # Make new image to paste text and receipt
    joined_img = Image.new(im_scaled.mode, (RECEIPT_RESIZE_WIDTH, scale_height + text_height),
                           (255, 255, 255))
    joined_img.paste(header_img_crop, (0, 0))
    header_img_crop.close()
    joined_img.paste(im_scaled, (0, text_height))
    im_scaled.close()

    # Save file to disk
    directory = "../data/receipts/"
    file_name = f'receipt_{receipt_number:05}.jpg'
    file_path = (Path(__file__).parent / (directory + file_name)).resolve()
    joined_img.save(file_path, format="JPEG")

    if show:
        joined_img.show()

    with BytesIO() as bio:
        joined_img.save(bio, format="JPEG")
        filedata = bio.getvalue()

    # Send email with file
    msg = EmailMessage()
    mail_name = EnvVars().get_mail_bot_name()
    mail_addr = EnvVars().get_mail_bot_address()
    mail_dest = EnvVars().get_destination_email()
    mail_password = EnvVars().get_mail_bot_password()
    msg["From"] = f'{mail_name} <{mail_addr}>'
    msg["To"] = mail_dest
    msg["Subject"] = file_name
    msg.set_content('\n'.join([text_1, text_2, text_3, text_4]))

    msg.add_attachment(filedata, 'image', 'jpeg', filename=file_name)

    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.login(mail_addr, mail_password)
    server.send_message(msg)
    server.quit()


# https://stackoverflow.com/a/67203353
def get_wrapped_text(text: str, font: ImageFont.FreeTypeFont,
                     line_length: int):
    lines = ['']
    for word in text.split():
        line = f'{lines[-1]} {word}'.strip()
        if font.getlength(line) <= line_length:
            lines[-1] = line
        else:
            lines.append(word)
    return '\n'.join(lines)


if __name__ == '__main__':
    # Test receipt processing
    EnvVars()
    process_receipt(
        # download_url = 'https://files.slack.com/files-pri/T92478E85-F05DWC1EP5Z/receipt.jpg',
        download_url=('https://files.slack.com/files-pri/T92478E85-F05QCMQ4T0S/'
                      'screenshot_20230829-114325.png'),
        uploader_name='Bobby B.',
        receipt_number=1234,
        message='This is a test. Please delete.',
        show=True
    )
