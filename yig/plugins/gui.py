import yig.config
import re
import json
import requests

from yig.bot import listener, KEY_MATCH_FLAG
from yig.util.data import get_user_param
from yig.util.view import divider_builder

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
    user_param = get_user_param(bot.team_id, bot.user_id)

    block_content = []

    block_content.append(build_input_content('Init your character sheet', "https://~"))
    block_content.append(build_button_content('update', 'Update your character sheet'))
    block_content.append(build_button_content('San Check', 'Your Sanity check'))
    block_content.append(build_radio_button_content(['HP', 'MP', 'SAN'], 'Change the ', ' of the character.'))

    block_content.append(divider_builder())

    block_content.append(build_skill_content(user_param))
    block_content.append(build_skill_content(user_param, 'hide '))
    block_content.append(build_param_content())

    block_content.append(divider_builder())

    block_content.append(build_button_content('join/leave session', 'session join or leave.'))
    block_content.append(build_button_content('update', 'Update your character sheet'))
    block_content.append(build_button_content('saveimg', 'Save your icon image'))
    block_content.append(build_button_content('help', 'More command'))

    block_content.append(divider_builder())

    view_content = {
        "type": "modal",
        "callback_id": "modal-identifier:%s" % bot.channel_id,
        "title": {
            "type": "plain_text",
            "text": "Call Of Cthulhu GUI Mode"
        },
        "submit": {
	    "type": "plain_text",
	    "text": "Init Your Charasheet.",
	    "emoji": True
	},
        "private_metadata": bot.channel_id,
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


@listener("VIEW_CONFIRM_SELECT_MODAL", KEY_MATCH_FLAG)
def gui_confirm_receiver(bot):
    """con"""
    command_url = "https://slack.com/api/views.push"
    user_param = get_user_param(bot.team_id, bot.user_id)

    block_content = []

    block_content.append(build_input_content('Init your character sheet', ""))
    block_content.append(build_plain_text_content("Do you want to add a correction value?"))
    view_content = {
        "type": "modal",
        "callback_id": "modal-identifier:%s" % bot.channel_id,
        "title": {
            "type": "plain_text",
            "text": "Call Of Cthulhu GUI Mode"
        },
        "submit": {
	    "type": "plain_text",
	    "text": "Init Your Charasheet.",
	    "emoji": True
	},
        "private_metadata": bot.channel_id,
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


def build_plain_text_content(text):
    return {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": text,
	    "emoji": true
	}
    }


def build_input_content(describe, initial_value):
    return {
        "type": "input",
	"element": {
	    "type": "plain_text_input",
            "initial_value": initial_value
	},
        "label": {
	    "type": "plain_text",
	    "text": describe,
	    "emoji": False
	}}


def build_skill_content(user_param, hide = ''):
    skill_list = []
    for k, v in user_param.items():
        if isinstance(v, list):
            skill_list.append((k, v[-1]))

    option_list = []
    for skill in skill_list:
        skill_name = skill[0]
        skill_targ = skill[1]
        if skill_name == "arms_name":
            break
        option_list.append({
	    "text": {
		"type": "plain_text",
                "text": f"{hide}{skill_name} <= {skill_targ}",
		"emoji": True
	    },
	    "value": f"{hide}{skill_name}" })
    skill_content = {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": f"Select the skill you want to {hide}roll"
	},
	"accessory": {
	    "type": "static_select",
	    "placeholder": {
		"type": "plain_text",
		"text": "List of skills you have",
		"emoji": True
	    },
	    "options": option_list
	}
    }
    return skill_content


def build_param_content():
    param_name_list = ["STR", "CON", "POW", "DEX", "APP", "SIZ", "INT", "EDU", "幸運", "知識", "アイデア"]
    param_list = []
    for param in param_name_list:
        param_list.append({
	    "text": {
		"type": "plain_text",
                "text": f"{param}",
		"emoji": True
	    },
	    "value": f"{param}" })

    param_content = {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": "Select the param you want to roll"
	},
	"accessory": {
	    "type": "static_select",
	    "placeholder": {
		"type": "plain_text",
		"text": "List of params you have",
		"emoji": True
	    },
	    "options": param_list
	}
    }
    return param_content


def build_radio_button_content(lst_button, prefix, surfix):
    lst = []
    for button in lst_button:
        lst.append({
	    "text": {
		"type": "plain_text",
		"text": f"{prefix}{button}{surfix}",
		"emoji": True,
	    },
	    "value": button
	})
    return {"type": "actions",
            "elements": [
	    {
                "type": "radio_buttons",
                "options": lst
            }
        ]
    }



def build_button_content(value, describe):
    return {
	"type": "section",
	"text": {
	    "type": "mrkdwn",
	    "text": describe
	},
	"accessory": {
	    "type": "button",
	    "text": {
		"type": "plain_text",
		"text": value,
		"emoji": True
	    },
	    "value": value
	}
    }
