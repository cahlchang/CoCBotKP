import yig.config
import re
import json
import requests

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
                "action_id": "modal-view-identifier",
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


@listener("VIEW_MODAL", KEY_MATCH_FLAG)
def gui_receiver(bot):
    """dui"""
    command_url = "https://slack.com/api/views.open"
    payload = {
        "token": bot.token,
        "channel": bot.channel_id
    }
    user_param = get_user_param(bot.team_id, bot.user_id)

    skill_list = []
    for k, v in user_param.items():
        if isinstance(v, list):
            skill_list.append((k, v[-1]))

    option_list = []
    cnt = 0
    for skill in skill_list:
        cnt += 1
        skill_name = skill[0]
        skill_targ = skill[1]
        if skill_name == "arms_name":
            break
        print(skill_name)
        option_list.append({
	    "text": {
		"type": "plain_text",
                "text": f"{skill_name} >= {skill_targ}",
		"emoji": True
	    },
	    "value": f"{skill_name}" })

    roll_content = {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": "Select the skill you want to roll"
	},
	"accessory": {
	    "type": "static_select",
	    "placeholder": {
		"type": "plain_text",
		"text": "Select an item",
		"emoji": True
	    },
	    "options": option_list
	}
    }
    block_content = []
    # block_content.append({
    #     "type": "section",
    #     "block_id": "charasheet_init",
    #     "text": {
    #         "type": "mrkdwn",
    #         "text": "init charasheet"
    #     },
    #     "accessory": {
    #         "type": "input",
    #         "text": {
    #             "type": "plain_text",
    #             "text": "https"
    #         },
    #         "action_id": "button-identifier"
    #     }
    # })
    block_content.append(roll_content)

    view_content = {
        "type": "modal",
        "callback_id": "modal-identifier",
        "title": {
            "type": "plain_text",
            "text": "Just a modal"
        },
        "blocks": block_content
    }

    payload = {
        "token": bot.token,
        "channel": bot.channel_id,
        "trigger_id": bot.trigger_id,
        "view": json.dumps(view_content, ensure_ascii=False)
    }

    print(payload)
    res = requests.post(command_url, data=payload)
    print(res.text)
