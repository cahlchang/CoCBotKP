import os
import json
import logging
import random
import traceback
import requests
import urllib.parse
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
        # todo redirectでワークスペースに飛ぶようにリダイレクト入れる
        return "ok"
    random.seed()
    body = event["body"]

    if "payload" in body:
        contents = body.split("=")
        payload_json = json.loads(urllib.parse.unquote(contents[-1]))

        if "modal-executed" in body:
            return None

        if "modal-view-identifier" in body or "ccmenustart" in body:
            bot.init_modal(body)
            return None

        if "actions" in payload_json \
           and ("static_select" in payload_json["actions"][0] \
           or "modal-confirm_button_with_sanc" in payload_json["actions"][0]):
            bot.confirm_modal(payload_json)
            return None

        if "modal-dispatch" in body:
            bot.modal_dispatch(body)
            return None
    else:
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
        payload = {
            "token": os.environ["WS_TOKEN"],
            "channel": 'CNCM21Z9T',
            "text": traceback.format_exc()
        }
        res = requests.get("https://slack.com/api/chat.postMessage?",
                           params=payload)
        print(res.text)
