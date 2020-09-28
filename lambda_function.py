import os
import json
import logging
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


def bootstrap(event: dict, _context) -> str:
    logging.info(json.dumps(event))
    bot = Bot()
    if "params" in event and "path" in event["params"]:
        bot.install_bot(event)
        # todo redirectでワークスペースに飛ぶように
        return "ok"
    random.seed()
    body = event["body"]
    logging.info(body)
    if "trigger_id" in body:
        bot.init_modal(body)
        return None

    body_split = body.split("&")
    evt_slack = {}
    for datum in body_split:
        lst = datum.split("=")
        evt_slack[lst[0]] = lst[1]

    if "subtype" in evt_slack:
        return None
    bot.init_param(evt_slack)
    bot.dispatch()
    return None


def lambda_handler(event: dict, _context) -> str:
    try:
        return bootstrap(event, _context)
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
