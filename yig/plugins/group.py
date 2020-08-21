from yig.bot import listener, RE_MATCH_FLAG, KEY_MATCH_FLAG
from yig.util.data import get_state_data, set_state_data, get_user_param, write_user_data, read_user_data

import yig.config
import re
import json
import random

KP_FILE_PATH = "kp.json"


@listener("kp+.*start", RE_MATCH_FLAG)
def session_start(bot):
    """:sparkles: *TRPG session start*\n`/cc kp start`"""
    color = yig.config.COLOR_ATTENTION
    set_start_session(bot.team_id, bot.user_id)
    return "セッションを開始します。\n参加コマンド\n`/cc join %s`" % bot.user_id, color


@listener("join+.*", RE_MATCH_FLAG)
def session_join(bot):
    """:+1: *join TRPG session*\n`/cc join [SESSION_ID]`"""
    color = yig.config.COLOR_ATTENTION
    state_data = get_state_data(bot.team_id, bot.user_id)
    kp_id = analyze_join_command(bot.key)
    if kp_id:
        add_gamesession_user(bot.team_id, kp_id, bot.user_id, state_data['pc_id'])
        state_data["kp_id"] = kp_id
        set_state_data(bot.team_id, bot.user_id, state_data)
        return "セッションに参加しました", color
    else:
        return "%s\nJOINコマンドが不正です" % bot.message, color


@listener("leave+.*", RE_MATCH_FLAG)
def session_leave(bot):
    """:wave: *leave TRPG session*\n`/cc leave [SESSION_ID]`"""
    color = yig.config.COLOR_ATTENTION
    state_data = get_state_data(bot.team_id, bot.user_id)
    kp_id = analyze_join_command(bot.key)
    if kp_id:
        reduce_gamesession_user(bot.team_id, kp_id, bot.user_id, state_data['pc_id'])
        state_data.pop("kp_id")
        set_state_data(bot.team_id, bot.user_id, state_data)
        return "セッションから退出しました", color
    else:
        return "%s\nLEAVEコマンドが不正です" % bot.message, color


@listener("kp.(order|sort).*", RE_MATCH_FLAG)
def session_member_order(bot):
    """:telescope:　*kp order member*\n`/cc order [PARAM]`\n`/cc sort [PARAM]`"""
    target_status = analyze_kp_order_command(bot.key)
    lst_user_data = get_lst_player_data(bot.team_id, bot.user_id, target_status)
    msg = f"{target_status}順\n"
    cnt = 0
    for user_data in lst_user_data:
        cnt += 1
        name = user_data["name"]
        v = user_data[target_status]
        msg += f"{cnt}, {name} ({v}) \n"
    return msg, yig.config.COLOR_ATTENTION


@listener("kp.select", RE_MATCH_FLAG)
def session_select_user(bot):
    """:point_left: *kp select member*\n`/cc select`"""
    body = read_user_data(bot.team_id, bot.user_id, KP_FILE_PATH)
    dict_kp = json.loads(body)
    lst_user = dict_kp["lst_user"]
    user_target = random.choices(lst_user)
    user_target_param = get_user_param(bot.team_id, user_target[0][0], user_target[0][1])
    return user_target_param["name"], yig.config.COLOR_ATTENTION


def set_start_session(team_id, user_id):
    """
    set_start_session function is starting game session.
    create s3 file.
    """
    write_user_data(team_id, user_id, KP_FILE_PATH, json.dumps({}, ensure_ascii=False))


def add_gamesession_user(team_id, kp_id, user_id, pc_id):
    body = read_user_data(team_id, kp_id, KP_FILE_PATH)
    dict_kp = json.loads(body)

    if "lst_user" not in dict_kp:
        dict_kp["lst_user"] = []

    dict_kp["lst_user"].append([user_id, pc_id])
    body_write = json.dumps(dict_kp, ensure_ascii=False).encode('utf-8')
    write_user_data(team_id, kp_id, KP_FILE_PATH, body_write)


def reduce_gamesession_user(team_id, kp_id, user_id, pc_id):
    body = read_user_data(team_id, kp_id, KP_FILE_PATH)
    dict_kp = json.loads(body)
    lst_reduce = []
    lst = [lst_joined for lst_joined in dict_kp["lst_user"] if lst_joined[0] != user_id]
    dict_kp["lst_user"] = lst
    body_write = json.dumps(dict_kp, ensure_ascii=False).encode('utf-8')
    write_user_data(team_id, kp_id, KP_FILE_PATH, body_write)


def get_lst_player_data(team_id, user_id, roll_targ):
    dict_kp = json.loads(read_user_data(team_id, user_id, KP_FILE_PATH).decode('utf-8'))
    lst_user = dict_kp["lst_user"]
    lst_user_param = []
    for user in lst_user:
        param = get_user_param(team_id, user[0], user[1])
        lst_user_param.append(
            {
                "name": param['name'],
                roll_targ: int(param[roll_targ])
            })

    lst_user_param.sort(key=lambda x: x[roll_targ])
    lst_user_param.reverse()
    return lst_user_param


def analyze_join_command(command: str) -> str:
    """
    analyze join command and return KP ID

    Examples:
        "JOIN UE63DUJJF" => "UE63DUJJF"
    """
    result = re.fullmatch(r"\S+\s+(\S+)", command)
    if result is None:
        return None
    return result.group(1)


def analyze_kp_order_command(command: str) -> str:
    """
    analyze KP ORDER command and return target status name

    Examples:
        "KP ORDER DEX" => "DEX"
        "KP ORDER 幸運" => "幸運"
    """
    result = re.fullmatch(r"KP\s+ORDER\s+(\S+)", command)
    if result is None:
        return None
    return result.group(1)

