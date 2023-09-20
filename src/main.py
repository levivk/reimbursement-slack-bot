#!/bin/env python3

from slack_bolt import App
from slack_bolt.context.say.say import Say
import logging
from pathlib import Path
from typing import List, Dict

from slack_handlers import handle_message, handle_reimbursement_post
import config


app = App(token=config.get_slack_bot_token(), signing_secret=config.get_slack_signing_secret())

logging.basicConfig(level=logging.INFO)


def handle_by_ts(ts: str) -> None:
    print("finding message with ts: " + ts)
    client = app.client
    result = client.conversations_history(channel="C9NG0FSG4", limit=10)
    msgs: List[Dict[str,str]] = result.get("messages", [])
    msg = None
    for m in msgs:
        if m["ts"] == ts:
            msg = m
            break

    if msg is None:
        print("ts not found")
        return

    print("found message from user: " + msg["user"])
    handle_reimbursement_post(msg, Say(client=client, channel="C9NG0FSG4"), client, msg)


def main() -> None:
    # Create data directory if needed
    (Path(__file__).parent / ("../data/receipts/")).resolve().mkdir(parents=True, exist_ok=True)

    # Check environment variables
    config.check_env_vars()

    # add listeners
    app.event({"type": "message"})(handle_message)
    app.start(port=3000)


if __name__ == "__main__":
    # handle_by_ts("1693522991.907009")
    main()
