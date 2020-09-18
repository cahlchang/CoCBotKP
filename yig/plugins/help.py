import botocore

from yig.bot import listener
from yig.util.data import get_user_param, get_state_data, get_now_status
from yig.util.view import get_pc_image_url, divider_builder, section_builder

import yig.config
import json


@listener("HELP")
def help(bot):
    """:question: *help message*\n`/cc help`"""
    channel = bot.user_id
    help_content = help_content_builder(bot.team_id, bot.user_id, bot.get_listener())
    return list(map(lambda c: dict(c, channel=channel), help_content)), None


@listener("OPENHELP")
def open_help(bot):
    """:school: *open help message*\n`/cc openhelp`"""
    help_content = help_content_builder(bot.team_id, bot.user_id, bot.get_listener())
    return help_content, None


def help_content_builder(team_id, user_id, listener):
    about = "This is the command to play Call of Cthulhu.\nEnjoy!"
    refer = "*<https://github.com/cahlchang/CoCNonKP/blob/main/command_reference.md|All Documents.>*\n\n"

    dict_function = {}
    for list_function in listener.values():
        for datum in list_function:
            if datum["function"].__name__ == "roll_skill" or datum["function"].__name__.startswith("easteregg"):
                continue
            dict_function[datum["function"].__name__] = datum["function"].__doc__

    user_param = None
    try:
        state_data = get_state_data(team_id, user_id)
        user_param = get_user_param(team_id, user_id, state_data["pc_id"])
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            print('new_participant')
        else:
            raise Exception(e)
    except Exception as e:
        raise Exception(e)

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
            }]

    skill_list = []
    if user_param is not None:
        block_content.append(divider_builder())
        pc_name = user_param['name']
        max_hp = user_param['HP']
        now_hp = get_now_status('HP', user_param, state_data)
        max_mp = user_param['MP']
        now_mp = get_now_status('MP', user_param, state_data)
        max_san = user_param['現在SAN']
        now_san = get_now_status('SAN', user_param, state_data, '現在SAN')
        db = user_param['DB']
        user_content = {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*PC INFO*\n\n*Name:* {pc_name}\n*HP:*  {now_hp}/{max_hp}  *MP:* {now_mp}/{max_mp}  *SAN:* {now_san}/{max_san}  *DB:*  {db}"
            },
            "accessory": {
                "type": "image",
                "image_url": get_pc_image_url(team_id, user_id, state_data["pc_id"], state_data['ts']),
                "alt_text": "image"
            }
        }
        block_content.append(user_content)
        for k, v in user_param.items():
            if isinstance(v, list):
                skill_list.append((k, v[-1]))

    block_content.append(divider_builder())

    block_content.append(section_builder([dict_function.pop('init_charasheet_with_vampire'),
                                          dict_function.pop('update_charasheet_with_vampire')]))

    block_content.append(section_builder([dict_function.pop('show_status'),
                                          dict_function.pop('update_user_status'),
                                          dict_function.pop('show_memo')]))

    block_content.append(divider_builder())

    block_content.append(section_builder([dict_function.pop('sanity_check'),
                                          dict_function.pop('dice_roll')]))

    block_content.append(section_builder([dict_function.pop('icon_save_image'),
                                          dict_function.pop('icon_load_image')]))

    block_content.append(section_builder([dict_function.pop('hide_roll'),
                                          dict_function.pop('show_list_chara')]))

    block_content.append(divider_builder())
    block_content.append(section_builder([dict_function.pop('session_start')]))

    lst_session = [k for k in dict_function.keys() if k.startswith('session')]
    lst_session_docs = list(map(dict_function.pop, lst_session))
    block_content.append(section_builder(lst_session_docs))

    block_content.append(divider_builder())
    block_content.append(section_builder(dict_function.values()))

    help_content = [{'blocks': json.dumps(block_content, ensure_ascii=False)}]
    if user_param is not None:
        help_content.extend(user_roll_help_content(skill_list, user_param, state_data))

    return help_content


def user_roll_help_content(skill_list, user_param, state_data):
    battle_content = search_content = action_content = negotiate_content = knowledge_content = None
    def lst_to_content(lst_content):
        lst = []
        i_pre = 0
        lst_message = []
        for i, content in enumerate(lst_content):
            skill_name = content[0]
            skill_targ = content[1]
            lst_message.append(f"*{skill_name}* (target point *{skill_targ}*)\n`/cc {skill_name} [+|-|*|/][number]`")
            if i > 0 and i % 9 == 0 or len(lst_content) == i + 1:
                lst.append(section_builder(lst_message))
                lst_message = []
                i_pre = i
        return lst

    i_pre = 0
    for i, skill in enumerate(skill_list):
        if skill[0] == '応急手当':
            battle_content = [divider_builder()]
            battle_content.append(section_builder([":crossed_swords: *battle roll*"]))
            battle_content.extend(lst_to_content(skill_list[0:i]))
            i_pre = i
        elif not search_content and skill[0].startswith('運転'):
            search_content = [divider_builder()]
            search_content.append(section_builder([":mag: *quest roll*"]))
            search_content.extend(lst_to_content(skill_list[i_pre:i]))
            i_pre = i
        elif not action_content and skill[0].startswith('言いくるめ'):
            action_content = [divider_builder()]
            action_content.append(section_builder([":hammer_and_wrench: *action roll*"]))
            action_content.extend(lst_to_content(skill_list[i_pre:i]))
            i_pre = i
        elif not negotiate_content and skill[0].startswith('医学'):
            negotiate_content = [divider_builder()]
            negotiate_content.append(section_builder([":money_with_wings: *negotiate roll*"]))
            negotiate_content.extend(lst_to_content(skill_list[i_pre:i]))
            i_pre = i
        elif not knowledge_content and skill[0].startswith('arms_name'):
            knowledge_content = [divider_builder()]
            knowledge_content.append(section_builder([":scales: *knowledge roll*"]))
            knowledge_content.extend(lst_to_content(skill_list[i_pre:i]))

    content = []

    for each_content in [battle_content, search_content, action_content, negotiate_content, knowledge_content]:
        content.append({'blocks': json.dumps(each_content, ensure_ascii=False)})
    return content

