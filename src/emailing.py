import config
from slack_handlers import REIMBURSEMENT_CHANNEL, BOT_DISPLAY_NAME, BOT_ICON
from storage import PersistentTable
from imap_tools import MailBox, MailboxLogoutError, MailboxLoginError  # type: ignore
from imap_tools import A, MailMessage  # type: ignore
import time
from datetime import datetime
import socket
import imaplib
from slack_sdk import WebClient
import traceback
from bs4 import BeautifulSoup
import re
import logging

logger = logging.getLogger(__name__)


RENEW_ACCOUNT_SECONDS = 29 * 60
IDLE_WAIT_SECONDS = 3 * 60
IMAP_POLL_PERIOD = 10
SUBJECT_FILTER_TEXT = "payment is scheduled for"
REGEX_SUB_FOR_NL = r"\s*\n+\s*"
INVOICE_NUMBER_KEY = "Invoice number"
ETA_KEY = "Payment delivery ETA"
ETA_DT_FMT = "%a, %B %d, %Y"  # https://docs.python.org/3/library/time.html#time.strftime


def test_receive() -> None:
    with MailBox("imap.gmail.com").login(  # type: ignore
        config.get_mail_bot_address(), config.get_mail_bot_password()
    ) as mbox:
        # in idle mode
        print("starting idle")
        mbox.idle.start()
        responses = mbox.idle.poll(timeout=60)
        mbox.idle.stop()
        # in not idle mode
        if responses:
            for msg in mbox.fetch(A(seen=False)):
                print(msg.date, msg.subject)
        else:
            print("no updates")


def emailing_thread() -> None:
    from slack_handlers import receipt_table

    logger.info("Starting emailing thread...")

    # Restart on unhandled exception
    while True:
        try:
            wait_for_reimbursement_processed_email(receipt_table)
        except BaseException as e:
            logger.error("Unhandled exception in emailing thread! Retrying...")
            logger.info(e)
            time.sleep(10)


# https://github.com/ikvk/imap_tools/blob/master/examples/idle.py
# TODO: check for new emails on starting
def wait_for_reimbursement_processed_email(table: PersistentTable) -> None:
    """
    Wait for an email from melio that the payment was processed. Respond to the slack message with
    the ETA.
    """

    def process_email(msg: MailMessage) -> None:
        """
        Parse an email, pull out the invoice number and eta, record the current time to storage,
        respond to slack with the eta
        """
        # Check subject line for test string
        if SUBJECT_FILTER_TEXT not in str(msg.subject):
            logger.warning(f"Unhandled email: {msg.from_} | {msg.subject}")
            return

        logger.info("New processed reimbursement email")

        # This is an email saying that a reimbursement is scheduled
        soup = BeautifulSoup(str(msg.html), "html.parser")
        text = soup.get_text()
        # This removes all the extra newlines and spaces
        text = re.sub(REGEX_SUB_FOR_NL, r"\n", text)
        text_split = text.split("\n")

        # try to get the invoice number and eta text.
        try:
            invoice_num_idx = text_split.index(INVOICE_NUMBER_KEY) + 1
            eta_idx = text_split.index(ETA_KEY) + 1
        except ValueError:
            # Email format changed!
            logger.error("Email format change! Could not find invoice or eta!")
            logger.error(text)
            return
        invoice_num_s = text_split[invoice_num_idx]
        eta = text_split[eta_idx]

        # Convert the value to their types
        try:
            invoice_num = int(invoice_num_s)
            # eta_datetime = datetime.strptime(eta, ETA_DT_FMT)
        except ValueError:
            # Couldn't convert!
            logger.error("Email format change! Could not parse invoice number!")
            logger.error(text)
            return

        # Get table and add eta
        with table.get_lock():
            # find invoice row in table
            row = None
            for r in table:
                if r["invoice"] == invoice_num:
                    row = r

            if row is None:
                # Invoice number not reported in slack?
                logger.error(f"Invoice number not reported in slack! {invoice_num_s}")
                return
            row["date_payment_sent"] = datetime.now()
            # sync because the table does not know the row changed
            # TODO: make change aware dictionary for table rows
            table.sync()

        # Respond to slack with eta
        slack_ts = row["slack_ts"]
        client = WebClient(token=config.get_slack_bot_token())
        msg_text = (
            "Your reimbursement has been processed. " f"It should arrive in your account on {eta}."
        )
        client.chat_postMessage(channel=REIMBURSEMENT_CHANNEL, thread_ts=slack_ts, text=msg_text, username=BOT_DISPLAY_NAME, icon_emoji=BOT_ICON)

        logger.info(f"Processed reimbursement #{invoice_num} to be received by {eta}")

    def do_idle() -> None:
        """
        Wait for emails and process them as they come
        """

        # # Fetch new messages
        # print('polling for emails...')
        # for msg in mbox.fetch(A(seen=False), mark_seen=True):
        #     process_email(msg)
        # # Wait to poll again
        # if stop_event is None:
        #     time.sleep(IMAP_POLL_PERIOD)
        # else:
        #     stop_event.wait(IMAP_POLL_PERIOD)
        #     if stop_event.is_set():
        #         raise KeyboardInterrupt

        responses = mbox.idle.wait(timeout=IDLE_WAIT_SECONDS)
        # print(time.asctime(), "IDLE responses:", responses)
        if responses:
            for msg in mbox.fetch(A(seen=False), mark_seen=True):
                process_email(msg)

    logger.info("Watching for emails.")
    # Continue until exited
    done = False
    while not done:
        start_time = time.monotonic()

        # login and wait for mail. Will fail on connection issue or interrupt
        try:
            mbox = MailBox("imap.gmail.com")  # type: ignore
            mbox.login(config.get_mail_bot_address(), config.get_mail_bot_password(), "INBOX")
            # log out every so often to renew the account
            while (time.monotonic() - start_time) < RENEW_ACCOUNT_SECONDS:
                try:
                    do_idle()
                except KeyboardInterrupt:
                    # Catch this here so we can logout
                    logger.info("Exiting...")
                    done = True
                    break
            mbox.logout()

        except (
            TimeoutError,
            ConnectionError,
            imaplib.IMAP4.abort,
            MailboxLoginError,
            MailboxLogoutError,
            socket.herror,
            socket.gaierror,
            socket.timeout,
        ) as e:
            logger.error(f"Error\n{e}\n{traceback.format_exc()}\nreconnect in a minute...")
            time.sleep(60)

        except KeyboardInterrupt:
            logger.info("Exiting...")
            break


def test() -> None:
    from datetime import datetime
    from pathlib import Path

    config.check_env_vars()

    csv_text = (
        "invoice,slack_ts,date_requested,date_payment_sent\n"
        "1,1693455608.170379,2023-08-30 23:20:12.263030,\n"
        "2,1693529827.684989,2023-08-31 19:57:13.360325,\n"
        "3,1693522991.907009,2023-08-31 20:24:22.757719,\n"
        "4,1693670781.780829,2023-09-02 11:06:27.422722,\n"
        "5,1693670853.728509,2023-09-02 11:07:38.515574,\n"
        "6,1693772872.554789,2023-09-03 15:27:57.750271,\n"
        "7,1693772894.334859,2023-09-03 15:28:18.675484,\n"
        "8,1693796721.311319,2023-09-03 22:05:26.318915,\n"
        "9,1694363637.201089,2023-09-10 11:34:03.225901,\n"
        "10,1694476521.809949,2023-09-11 18:55:27.754917,\n"
        "11,1694481987.479399,2023-09-11 20:26:32.929845,\n"
        "12,1694485632.630099,2023-09-11 21:27:16.183624,\n"
        "13,1695005731.560779,2023-09-17 21:55:36.020494,\n"
        "14,1695086848.113869,2023-09-18 20:27:32.497222,\n"
        "15,1695092292.071469,2023-09-18 21:58:16.601005,\n"
    )

    def convert_date(s: str) -> None | datetime:
        if s == "":
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

    with open(csv_path, "w") as f:
        f.write(csv_text)

    table = PersistentTable(
        str(csv_path), fieldnames=list(converters.keys()), converters=converters
    )

    wait_for_reimbursement_processed_email(table)

    with open(csv_path, "r") as f:
        print(str(f.read()))


def thread_test() -> None:
    import threading

    try:
        t = threading.Thread(target=emailing_thread, daemon=True)
        t.start()
        time.sleep(2000)
    except (KeyboardInterrupt, SystemExit):
        print("Received interrupt, exiting")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    thread_test()
