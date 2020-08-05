from yig.bot import listener
from yig.util import get_user_param

import yig.config
import json


@listener("HELP")
def help(bot):
    """:question: *help message*
`/cc help`
    """
    about = "This is the command to play Call of Cthulhu.\nEnjoy!"
    refer = "*<https://github.com/cahlchang/CoCNonKP/blob/master/command_reference.md|All Documents.>*\n\n"
    getstatus = ":eyes: *show status*\n`/cc s`\n`/cc status`"
    sanc = ":ghost: *san check*\n`/cc sanc`\n`/cc sanc [safe_point]/[fail_point]`"

    dict_function = {}
    for list_function in bot.get_listener().values():
        for datum in list_function:
            dict_function[datum["function"].__name__] = datum

    func_init_vampire = dict_function.pop('init_charasheet_with_vampire')
    func_update_vampire = dict_function.pop('update_charasheet_with_vampire')

    user_param = get_user_param(bot.user_id)

    block_content = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": about
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": refer
                }
            },
            {
                "type": "divider"
            }]

    skill_list = []
    if user_param is not None:
        pc_name = user_param['name']
        now_hp = user_param['HP']
        user_content = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Name* \n{pc_name}\n\n*HP* {now_hp}/{now_hp}"
            },
            "accessory": {
                "type": "image",
                "image_url": bot.data_user["profile"]["image_512"],
                "alt_text": "computer thumbnail"
            }
        }
        block_content.append(user_content)
        for k, v in user_param.items():
            if isinstance(v, list):
                skill_list.append((k, v[-1]))

    common_content = [
        {
            "type": "divider"
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": func_init_vampire["function"].__doc__
                },
                {
                    "type": "mrkdwn",
                    "text": func_update_vampire["function"].__doc__
                }
            ]
        },
        {
                "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": getstatus
            },
        },
        {
            "type": "divider"
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": sanc
            },
        },
        {
            "type": "divider"
        }]
    block_content.extend(common_content)
    skill_content = []
    cnt = 0
    if skill_list:
        for skill in skill_list:
            cnt += 1
            skill_name = skill[0]
            skill_targ = skill[1]
            skill_content.append({"type": "mrkdwn",
                                  "text": f"*{skill_name}* (target point *{skill_targ}*)\n`/cc {skill_name}  [+-*/][number]`"})
            if cnt == 10:
                break
        block_content.append({"type": "section",
                              "fields": skill_content})

    add_content = []
    cnt = 0
    for k, v in dict_function.items():
        if k.startswith('easteregg'):
            continue
        cnt += 1
        add_content.append({"type": "mrkdwn",
                            "text": v["function"].__doc__})
        if cnt == 8:
            break
    block_content.append({"type": "section",
                          "fields": add_content})

    help_content = {
        'blocks': json.dumps(block_content)
    }
    return help_content, None

