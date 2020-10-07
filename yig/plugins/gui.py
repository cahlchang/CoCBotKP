import yig.config
import re
import json
import requests
import logging
from datetime import datetime

from yig.bot import listener, KEY_MATCH_FLAG
from yig.util.data import get_user_param, write_user_data, read_user_data
from yig.util.view import divider_builder


@listener("", KEY_MATCH_FLAG)
def gui_hook(bot):
    """gui test"""
    logger = logging.getLogger()
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
    block_content.append(build_channel_select_content())
    # 'Init your character sheet'
    block_content.append(build_input_content('キャラクターシートのURLからデータを初期化します', "https://~"))
    # Update your character sheet
    block_content.append(build_button_content('update', 'キャラクターシートの変更点を反映させます', "modal-dispatch_go_button_0"))
    # Your Sanity check
    block_content.append(build_button_content('SAN Check', 'SANチェックを行います', "modal-confirm_button_with_sanc"))
    # Change the , of the character.
    block_content.append(build_radio_button_content(['HP', 'MP', 'SAN'], 'PCの', 'を変更します'))

    block_content.append(divider_builder())

    block_content.append(build_skill_content(user_param))
    block_content.append(build_skill_content(user_param, 'hide '))
    block_content.append(build_param_content())

    block_content.append(divider_builder())

    # session join or leave.
    block_content.append(build_button_content('join/leave session', 'セッションに参加/離脱します', "bym2"))
    # Save your icon image
    block_content.append(build_button_content('saveimg', 'アイコンの画像を保存します', "modal-dispatch_go_button_1"))
    # More command
    block_content.append(build_button_content('help', 'それ以外のコマンドを確認します', "modal-dispatch_go_button_2"))

    block_content.append(divider_builder())
    now = datetime.now()
    view_content = {
        "type": "modal",
        "callback_id": "modal-identifier",
        "title": {
            "type": "plain_text",
            "text": "Call Of Cthulhu GUI Mode"
        },
        "submit": {
	    "type": "plain_text",
	    "text": "Init Your Charasheet.",
	    "emoji": True
	},
        "blocks": block_content
    }

    payload = {
        "token": bot.token,
        "trigger_id": bot.trigger_id,
        "view": json.dumps(view_content, ensure_ascii=False)
    }

    res = requests.post(command_url, data=payload)
    res_json = json.loads(res.text)
    logging.info(json.dumps(res_json))
    for k, data in res_json["view"]["state"]["values"].items():
        for kk, datum in data.items():
            if datum["type"] == "conversations_select":
                bot.channel_id = datum["selected_conversation"]

    write_user_data(bot.team_id, bot.user_id, "key_id", json.dumps({"view_id": res_json["view"]["id"], "channel_id": bot.channel_id}))


@listener("VIEW_CONFIRM_SELECT_MODAL", KEY_MATCH_FLAG)
def gui_confirm_select_receiver(bot):
    """con"""
    command_url = "https://slack.com/api/views.update"
    user_param = get_user_param(bot.team_id, bot.user_id)

    block_content = []
    bot.key = bot.key.replace('+', ' ')
    # "Do you want to add a correction value?\n"
    # "For example\n"
    # "%s+10, %s-20, %s*2, %s/2" % (bot.key, bot.key, bot.key, bot.key)
    block_content.append(build_plain_text_content(("ロールの補正値がある場合、補正値を入れて下さい\n"
                                                   "例)\n"
                                                   "%s+10, %s-20, %s*2, %s/2" % (bot.key, bot.key, bot.key, bot.key))))
    block_content.append(build_input_content('Roll correction value', "%s" % bot.key))
    map_id = json.loads(read_user_data(bot.team_id, bot.user_id, "key_id"))
    view_id = map_id["view_id"]
    channel_id = map_id["channel_id"]
    view_content = {
        "type": "modal",
        "callback_id": "modal-dispatch_in_select",
        "title": {
            "type": "plain_text",
            "text": "Call Of Cthulhu GUI Mode"
        },
        "submit": {
	    "type": "plain_text",
	    "text": "Roll!",
	    "emoji": True
	},
        "private_metadata": channel_id,
        "blocks": block_content
    }

    payload = {
        "token": bot.token,
        "channel": channel_id,
        "trigger_id": bot.trigger_id,
        "view_id": view_id,
        "private_metadata": channel_id,
        "response_action": "clear",
        "view": json.dumps(view_content, ensure_ascii=False)
    }

    res = requests.post(command_url, data=payload)
    logging.info(json.dumps(res.text))


@listener("VIEW_CONFIRM_EXECUTED_MODAL", KEY_MATCH_FLAG)
def gui_confirm_delete(bot):
    """con"""
    command_url = "https://slack.com/api/views.update"
    map_id = json.loads(read_user_data(bot.team_id, bot.user_id, "key_id"))
    view_id = map_id["view_id"]
    channel_id = map_id["channel_id"]
    block_content = []
    block_content.append(build_plain_text_content("command execute done."))
    view_content = {
        "type": "modal",
        "callback_id": "modal-executed",
        "title": {
            "type": "plain_text",
            "text": "COMPLETE!"
        },
        "private_metadata": channel_id,
	"close": {
	    "type": "plain_text",
	    "text": "OK",
	    "emoji": True
	},
        "blocks": block_content
    }

    payload = {
        "token": bot.token,
        "trigger_id": bot.trigger_id,
        "view_id": view_id,
        "response_action": "clear",
        "view": json.dumps(view_content, ensure_ascii=False)
    }
    res = requests.post(command_url, data=payload)
    print(res.text)


@listener("VIEW_CONFIRM_SANC_MODAL", KEY_MATCH_FLAG)
def gui_confirm_sanc(bot):
    """con"""
    command_url = "https://slack.com/api/views.update"
    map_id = json.loads(read_user_data(bot.team_id, bot.user_id, "key_id"))
    view_id = map_id["view_id"]
    channel_id = map_id["channel_id"]
    block_content = []
    # EN
    # "Enter the required SAN check value. `sanc [success]/[fail]`\n"
    # "If you only want to check the SAN, just [GO!] ahead\n"
    # "For example\n"
    # "sanc 0/1, sanc 1/1d6, 1d20/1d100"
    block_content.append(build_mrkdwn_content(("SANチェックの値を入力して下さい。`sanc [成功量]/[失敗量]`\n"
                                               "もしSANチェックのみを行う場合、そのまま「GO!」ボタンを押して下さい\n"
                                               "例)\n"
                                               "sanc 0/1, sanc 1/1d6, 1d20/1d100")))
    # Write the value of the SAN check
    block_content.append(build_input_content("SANチェックの値を入力して下さい", 'sanc'))
    view_content = {
        "type": "modal",
        "callback_id": "modal-dispatch_in_sanc",
        "title": {
            "type": "plain_text",
            "text": "SAN CHECK MODAL"
        },
        "private_metadata": channel_id,
        "submit": {
	    "type": "plain_text",
	    "text": "GO!",
	    "emoji": True
	},
	"close": {
	    "type": "plain_text",
	    "text": "CLOSE",
	    "emoji": True
	},
        "blocks": block_content
    }

    payload = {
        "token": bot.token,
        "trigger_id": bot.trigger_id,
        "view_id": view_id,
        "response_action": "clear",
        "view": json.dumps(view_content, ensure_ascii=False)
    }
    res = requests.post(command_url, data=payload)
    print(res.text)


@listener("VIEW_CONFIRM_UPDATE_STATUS_MODAL", KEY_MATCH_FLAG)
def gui_confirm_status(bot):
    """con"""
    command_url = "https://slack.com/api/views.update"
    map_id = json.loads(read_user_data(bot.team_id, bot.user_id, "key_id"))
    view_id = map_id["view_id"]
    channel_id = map_id["channel_id"]
    block_content = []
    block_content.append(build_mrkdwn_content(("ステータスの変更を入力して下さい\n",
                                               "例)\n",
                                               "2点ダメージを回復する場合。`u HP+2`\n",
                                               "5点MPを払う場合。`u MP-5`\n"
                                               "3点のSANを減らす場合。`u SAN-3`")))
    block_content.append(build_input_content("変更を入力して下さい", 'u %s' % bot.key))
    view_content = {
        "type": "modal",
        "callback_id": "modal-confirm_button_with_status",
        "title": {
            "type": "plain_text",
            "text": "STATUS UPDATE MODAL"
        },
        "private_metadata": channel_id,
        "submit": {
	    "type": "plain_text",
	    "text": "UPDATE",
	    "emoji": True
	},
	"close": {
	    "type": "plain_text",
	    "text": "CLOSE",
	    "emoji": True
	},
        "blocks": block_content
    }

    payload = {
        "token": bot.token,
        "trigger_id": bot.trigger_id,
        "view_id": view_id,
        "response_action": "clear",
        "view": json.dumps(view_content, ensure_ascii=False)
    }
    res = requests.post(command_url, data=payload)
    print(res.text)


def build_channel_select_content():
    return {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": "Post channel"
	},
	"accessory": {
	    "type": "conversations_select",
            "action_id": "modal-dispatch-no-trans-channel",
            "default_to_current_conversation": True,
	    "placeholder": {
		"type": "plain_text",
		"text": "text",
		"emoji": True
	    },
	    "filter": {
		"include": [
		    "private",
                    "public"
		]
	    }
        }
    }


def build_plain_text_content(text):
    return {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": text,
	    "emoji": True
	}
    }


def build_mrkdwn_content(text):
    return {
	"type": "section",
	"text": {
	    "type": "mrkdwn",
	    "text": text
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

    if hide != '':
        text_section = "ロールを振りたい技能を選択して下さい"
    else:
        text_section = "秘匿でロールを振りたい技能を選択して下さい。結果はKPにのみ届きます。"
        #"List of skills you have"
    skill_content = {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": text_section
	},
	"accessory": {
	    "type": "static_select",
	    "placeholder": {
		"type": "plain_text",
		"text": "所持技能リスト",
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

    # Select the param you want to roll
    # List of params you have
    param_content = {
	"type": "section",
	"text": {
	    "type": "plain_text",
	    "text": "ロールを振りたいパラメータを選択して下さい"
	},
	"accessory": {
	    "type": "static_select",
	    "placeholder": {
		"type": "plain_text",
		"text": "パラメータリスト",
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


def build_button_content(value, describe, action_id):
    return {
	"type": "section",
	"text": {
	    "type": "mrkdwn",
	    "text": describe
	},
	"accessory": {
	    "type": "button",
            "action_id": action_id,
	    "text": {
		"type": "plain_text",
		"text": value,
		"emoji": True
	    },
	    "value": value
	}
    }
