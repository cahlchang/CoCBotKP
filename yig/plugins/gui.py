import yig.config
import re
import json


from yig.bot import listener, KEY_MATCH_FLAG
from yig.util.data import get_user_param


@listener("", KEY_MATCH_FLAG)
def gui_hook(bot):
    """gui test"""
    block_content = [
        {
            "type": "section",
            "block_id": "section-identifier",
            "text": {
                "type": "plain_text",
                "text": "CoC gui button"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Push button",
                },
                "action_id": "button-identifier",
            }
        }
    ]
    payload = {
        "type": "modal",
        "callback_id": "modal-identifier",
        "title": {
            "type": "plain_text",
            "text": "Just a modal"
        },
        'blocks': json.dumps(block_content, ensure_ascii=False)}
    return payload, None


@listener("gui modal view", KEY_MATCH_FLAG)
def gui_receiver(bot):
    """dui"""
    block_content = [
        {
            "type": "section",
            "block_id": "section-identifier",
            "text": {
                "type": "mrkdwn",
                "text": "*Welcome* to ~my~ Block Kit _modal_!"
            },
            "accessory": {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Just a button"
                },
                "action_id": "button-identifier"
            }
        }
    ]

    payload = {
        "trigger_id": bot.trigger_id,
        "view": {
            "type": "modal",
            "callback_id": "modal-identifier",
            "title": {
                "type": "plain_text",
                "text": "Just a modal"
                }
            },
            'blocks': json.dumps(block_content, ensure_ascii=False)}

    return payload, None
