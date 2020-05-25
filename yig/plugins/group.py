from yig.bot import listener, RE_MATCH_FLAG
from yig.util import get_state_data, set_state_data, get_user_param

import boto3
import yig.config
import re
import json

KP_FILE_PATH = "/kp.json"

@listener("kp+.*start", RE_MATCH_FLAG)
def start_session(bot):
    color = yig.config.COLOR_ATTENTION
    set_start_session(bot.user_id)
    return "セッションを開始します。\n参加コマンド\n```/cc join %s```" % bot.user_id, color


@listener("join+.*", RE_MATCH_FLAG)
def join_session(bot):
    color = yig.config.COLOR_ATTENTION
    state_data = get_state_data(bot.user_id)
    kp_id = analyze_join_command(bot.key)
    if kp_id:
        add_gamesession_user(kp_id, bot.user_id, state_data["pc_id"])
        state_data["kp_id"] = kp_id
        set_state_data(bot.user_id, state_data)
        return "セッションに参加しました", color
    else:
        return "%s\nJOINコマンドが不正です" % bot.message, color


@listener("kp+.*order.*", RE_MATCH_FLAG)
def order_member(bot):
    color = yig.config.COLOR_ATTENTION
    target_status = analyze_kp_order_command(bot.key)
    lst_user_data = get_lst_player_data(bot.user_id, target_status)
    msg = f"{target_status}順\n"
    cnt = 0
    for user_data in lst_user_data:
        cnt += 1
        name = user_data["name"]
        v = user_data[target_status]
        msg += f"{cnt}, {name} ({v}) \n"
    return msg, color


def set_start_session(user_id):
    """
    set_start_session function is starting game session.
    create s3 file.
    """
    key_session = user_id + KP_FILE_PATH
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    obj_session = bucket.Object(key_session)
    body_session = json.dumps({}, ensure_ascii=False)
    obj_session.put(
        Body=body_session.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )


def add_gamesession_user(kp_id, user_id, pc_id):
    key_kp_file = kp_id + KP_FILE_PATH
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    obj_kp_file = bucket.Object(key_kp_file)
    response = obj_kp_file.get()
    body = response['Body'].read()
    dict_kp = json.loads(body.decode('utf-8'))

    if "lst_user" not in dict_kp:
        dict_kp["lst_user"] = []

    dict_kp["lst_user"].append([user_id, pc_id])
    body_session = json.dumps(dict_kp, ensure_ascii=False)
    response = obj_kp_file.put(
        Body=body_session.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )


def get_lst_player_data(user_id, roll_targ):
    key_kp_file = user_id + KP_FILE_PATH
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    obj_kp_file = bucket.Object(key_kp_file)
    response = obj_kp_file.get()
    body = response['Body'].read()
    dict_kp = json.loads(body.decode('utf-8'))
    lst_user = dict_kp["lst_user"]
    lst_user_param = []
    for user in lst_user:
        param = get_user_params(user[0], user[1])
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

