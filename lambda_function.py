import os
import json
import logging
import urllib.request
import urllib.parse
import random
import traceback
import requests
from yig.bot import Bot

"""
Slack Bot function for CoC TRPG.
This is deployed on AWS Lambda

[terms]
state: PC's HP, MP, SAN, キャラクター保管庫URL, etc...
"""

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def format_as_command(text: str) -> str:
    """
    Make text uppercased and remove edge spaces
    """
    return text.upper().strip()


def bootstrap(event: dict, _context) -> str:
    logging.info(json.dumps(event))
    bot = Bot()
    if "params" in event and "path" in event["params"]:
        bot.install_bot(event)
        # todo redirectでワークスペースに飛ぶように
        return "ok"
    random.seed()
    body = event["body"]
    body_split = body.split("&")
    evt_slack = {}
    for datum in body_split:
        lst = datum.split("=")
        evt_slack[lst[0]] = lst[1]
    user_id = evt_slack["user_id"]

    response_url = urllib.parse.unquote(evt_slack["response_url"])
    if "subtype" in evt_slack:
        return None

    message = urllib.parse.unquote_plus(evt_slack["text"])
    if message.split(' ') and message.split(' ')[-1].isnumeric():
        message = ' '.join(message.split(' ')[:-1]) + "+" + message.split(' ')[-1]
    channel_id = urllib.parse.unquote(evt_slack["channel_id"])
    team_id = urllib.parse.unquote(evt_slack["team_id"])

    key = format_as_command(message)

    bot.init_param(user_id,
                   response_url,
                   key,
                   message,
                   channel_id,
                   team_id)
    bot.dispatch()


def lambda_handler(event: dict, _context) -> str:
    try:
        bootstrap(event, _context)
    except Exception as e:
        channel_id = 'CNCM21Z9T'
        payload = {
            "token": os.environ["WS_TOKEN"],
            "channel": channel_id,
            "text": traceback.format_exc()
        }
        res = requests.get("https://slack.com/api/chat.postMessage?",
                           params=payload)
        print(res.text)
