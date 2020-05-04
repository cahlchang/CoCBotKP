import os
import json
import logging
import urllib.request
import urllib.parse
import re
import random
import math
from concurrent import futures
import unicodedata
from typing import List, Tuple
import traceback

import boto3
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


AWS_S3_BUCKET_NAME = 'wheellab-coc-pcparams'
STATE_FILE_PATH = "/state.json"
KP_FILE_PATH = "/kp.json"

COLOR_CRITICAL = '#EBB424'
COLOR_SUCCESS = '#36a64f'
COLOR_FAILURE = '#E01E5A'
COLOR_FUMBLE = '#3F0F3F'
COLOR_ATTENTION = '#80D2DE'

lst_trigger_param = ["HP", "MP"]


def build_response(message):
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "body": json.dumps({
            "icon_emoji": "books",
            "text": "未対応のメッセージです。/cc helpで確認ください。"
        })
    }


def get_user_params(user_id, pc_id=None):
    key = ""
    if pc_id is None:
        dict_state = get_dict_state(user_id)
        key = user_id + "/" + dict_state["pc_id"] + ".json"
    else:
        key = user_id + "/" + pc_id + ".json"
    s3obj = boto3.resource('s3')
    bucket = s3obj.Bucket(AWS_S3_BUCKET_NAME)

    obj = bucket.Object(key)
    response = obj.get()
    body = response['Body'].read()
    return json.loads(body.decode('utf-8'))


def get_dict_state(user_id):
    """
    get_dict_state function is get state file.
    """

    key_state = user_id + STATE_FILE_PATH

    s3obj = boto3.resource('s3')
    bucket = s3obj.Bucket(AWS_S3_BUCKET_NAME)

    obj = bucket.Object(key_state)
    response = obj.get()
    body = response['Body'].read()
    return json.loads(body.decode('utf-8'))


def set_state(user_id, dict_state):
    key_state = user_id + STATE_FILE_PATH

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)

    obj_state = bucket.Object(key_state)
    body_state = json.dumps(dict_state, ensure_ascii=False)
    response = obj_state.put(
        Body=body_state.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )
    # TODO: エラー処理すべき
    logging.info(f"Fail to put state to S3. response:[{response}]")


def set_start_session(user_id, kp_name):
    key_session = user_id + KP_FILE_PATH
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)

    obj_session = bucket.Object(key_session)
    body_session = json.dumps({}, ensure_ascii=False)
    obj_session.put(
        Body=body_session.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )

    url = "https://slack.com/api/users.profile.set"
    set_params = {'token': os.environ["TOKEN"],
                  'user': user_id,
                  'profile': json.dumps(
                      {
                          "display_name": kp_name
                      }
                  )}
    headers = {'Content-Type': 'application/json'}
    r = requests.get(url, params=set_params, headers=headers)
    print(r.text)


def add_gamesession_user(kp_id, user_id, pc_id):
    key_kp_file = kp_id + KP_FILE_PATH
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
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
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
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


def set_user_params(user_id, url, is_update=False):
    logging.info("request start")
    pc_id = url.split("/")[-1]

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = res.read().decode('utf-8')
    logging.info("request end")

    name = ''
    dict_param = {}
    dict_param['user_id'] = user_id
    dict_param['pc_id'] = pc_id

    is_param_end = False
    is_param_parse = False
    is_param_now_parse = False
    lst_param = []

    is_san_end = False

    is_role_end = False
    is_role_now_parse = False
    role_now_parse = ""

    # TODO 関数処理化してもう少し早くはできるが…
    logging.info("regexp start")
    lst = body.splitlines()
    for line in lst:
        if not is_param_end:
            if re.match('.*<div class="disp"><table class="pc_making">.*', line):
                is_param_parse = True

            if is_param_parse:
                if re.match(r'.*<th colspan="2">現在値</th>.*', line):
                    is_param_now_parse = True

            if is_param_now_parse:
                if re.match(r'/*</tr>.*', line):
                    lst = ["STR", "CON", "POW", "DEX", "APP", "SIZ", "INT",
                        "EDU", "HP", "MP", "初期SAN", "アイデア", "幸運", "知識"]
                    lst_tmp = []
                    for raw_param in lst_param:
                        m = re.match('.*value="(.*?)".*', raw_param)
                        if m:
                            lst_tmp.append(m.group(1))

                    for name_param in lst:
                        dict_param[name_param] = lst_tmp.pop(0)
                    is_param_end = True

                lst_param.append(line)
            continue

        if not is_san_end:
            if re.match(".*SAN_Left.*", line):
                is_san_end = True
                m = re.match('.*value="(.*?)".*', line)
                dict_param["現在SAN"] = m.group(1)
                continue

        if not is_role_end and is_san_end:
            m = re.match('.*(cTBAU|cTFAU|cTAAU|cTCAU|cTKAU).*', line)
            if m:
                is_role_now_parse = True
                continue

            if is_role_now_parse:
                if "" == role_now_parse:
                    m = re.match(r'.*<th>(.*)</th>.*', line)
                    if m:
                        role_now_parse = m.group(1)
                        continue

                if role_now_parse not in dict_param:
                    dict_param[role_now_parse] = []

                m = re.match('.*value="(.*?)".*', line)
                if m:
                    dict_param[role_now_parse].append(m.group(1))
                else:
                    dict_param[role_now_parse].append(0)

            m = re.match('.*(TBAP|TFAP|TAAP|TCAP|TKAP).*', line)
            if m:
                is_role_now_parse = False
                role_now_parse = ""
                continue

            m = re.match('.*btnDelLineKnowArts.*', line)
            if m:
                is_role_end = True

        if '' == name and is_role_end:
            m = re.match(
                '.*<input name="pc_name" class="str" id="pc_name" size="55" type="text" value="(.*)">.*', line)
            if m:
                dict_param["name"] = m.group(1)

            continue

    logging.info("regexp end")
    dict_temp = {}
    lst_remove = []
    dict_replace = {
        "unten_bunya": "運転（{}）",
        "geijutu_bunya": "芸術（{}）",
        "seisaku_bunya": "製作（{}）",
        "main_souju_norimono": "操縦（{}）",
        "mylang_name": "母国語（{}）",
        "Name[]": "{}"
    }
    for key in dict_param.keys():
        for proc, key_new in dict_replace.items():
            if proc in key:
                m2 = re.match(r'.*value="(.*?)" s.*', key)
                if m2:
                    key_new = key_new.format(m2.group(1))
                    dict_temp[key_new] = dict_param[key]

                lst_remove.append(key)

    dict_param.update(dict_temp)

    for key_remove in lst_remove:
        del dict_param[key_remove]

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)

    logging.info("puts3 start")
    key = user_id + "/" + pc_id + ".json"
    # TODO 保存処理を関数に出す
    obj = bucket.Object(key)
    body = json.dumps(dict_param, ensure_ascii=False)
    response = obj.put(
        Body=body.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )

    if is_update:
        return dict_param

    key_state = user_id + STATE_FILE_PATH
    dict_state = {
        "url": url,
        "pc_id": dict_param["pc_id"]
    }
    obj_state = bucket.Object(key_state)
    body_state = json.dumps(dict_state, ensure_ascii=False)
    response = obj_state.put(
        Body=body_state.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )

    logging.info(f"puts3 2 end. response:[{response}]")
    return dict_param


def get_status_message(message_command, dict_param, dict_state):
    name = dict_param['name']

    c_hp = dict_param["HP"]
    if "HP" in dict_state:
        t_hp = dict_state["HP"]
        val_hp = eval(f"{c_hp} + {t_hp}")
    else:
        val_hp = dict_param["HP"]

    c_mp = dict_param["MP"]
    if "MP" in dict_state:
        t_mp = dict_state["MP"]
        val_mp = eval(f"{c_mp} + {t_mp}")
    else:
        val_mp = dict_param["MP"]

    dex = dict_param["DEX"]

    c_san = dict_param["現在SAN"]
    if "SAN" in dict_state:
        t_san = dict_state["SAN"]
        val_san = eval(f"{c_san} + {t_san}")
    else:
        val_san = dict_param["現在SAN"]

    return f"【{name}】{message_command}\nHP {val_hp}/{c_hp}　　MP {val_mp}/{c_mp}　　DEX {dex}　　SAN {val_san}/{c_san}"


def return_param(response_url, user_id, return_message, color, response_type="in_channel"):
    payload = {
        "icon_emoji": "books",
        "response_type": response_type,
        "replace_original": False,
        "headers": {},
        "text": "<@{}>".format(user_id),
        "attachments": json.dumps([
            {
                "text": return_message,
                "type": "mrkdwn",
                "color": color
            }
        ])}

    res = requests.post(response_url, data=json.dumps(payload))
    print(res.url)
    print(res.text)


def post_command(message, token, data_user, channel_id, is_replace_plus=False):
    command_url = "https://slack.com/api/chat.postMessage?"
    command_string = message
    if is_replace_plus:
        command_string = message.replace("+", " ")

    payload = {
        "token": token,
        # "as_user": True,
        "username": data_user["profile"]["display_name"],
        "icon_url": data_user["profile"]["image_1024"],
        "channel": channel_id,
        "text": f"/cc {command_string}"
    }
    print(payload)
    res = requests.get(command_url, params=payload)
    print(res.url)


def judge_1d100(target: int, dice: int):
    """"
    Judge 1d100 dice result, and return text and color for message.
    Result is critical, success, failure or fumble.
    Arguments:
        target {int} -- target value (ex. skill value)
        dice {int} -- dice value
    Returns:
        message {string}
        rgb_color {string}
    """
    if dice <= target:
        if dice <= 5:
            return "クリティカル", COLOR_CRITICAL
        return "成功", COLOR_SUCCESS

    if dice >= 96:
        return "ファンブル", COLOR_FUMBLE
    return "失敗", COLOR_FAILURE


def split_alternative_roll_or_value(cmd) -> Tuple[str, str]:
    """
    Split text 2 roll or value.
    Alternative roll is like following.
    - 0/1
    - 1/1D3
    - 1D20/1D100

    Arguments:
        cmd {str} -- command made by upper case
    Returns:
        tuple of 2 str or None
    """
    element_matcher = r"(\d+D?\d*)"
    result = re.fullmatch(f"{element_matcher}/{element_matcher}", cmd)
    if result is None or len(result.groups()) != 2:
        return None
    return result.groups()


def eval_roll_or_value(text: str) -> List[int]:
    """
    Evaluate text formated roll or value.
    If invalid format text is passed, just return [0].
    For dice roll, return values as list.
    Arguments:
        text {str} -- expect evaluatable text
                   examples: "1", "1D3", "2D6"
    Returns:
        List[int] -- evaluated values
    """
    try:
        return [int(text)]
    except ValueError:
        dice_matcher = re.fullmatch(r"(\d+)D(\d+)", text)
        if dice_matcher is None:
            return [0]
        match_numbers = dice_matcher.groups()
        dice_count = int(match_numbers[0])
        dice_type = int(match_numbers[1])
        if dice_count < 0 or dice_type < 0:
            return [0]
        return roll_dice(dice_count, dice_type)


def roll_dice(dice_count: int, dice_type: int) -> List[int]:
    """
    Get multiple and various dice roll result.
    ex) `roll_dice(2, 6)` means 2D6 and return each result like [2, 5].
    Arguments:
        dice_count {int} -- [description]
        dice_type {int} -- [description]
    Returns:
        List[int] -- All dice results
    """
    results = []
    for _ in range(dice_count):
        results.append(random.randint(1, dice_type))
    return results


def format_as_command(text: str) -> str:
    """
    Make text uppercased and remove edge spaces
    """
    return text.upper().strip()


def get_sanc_result(cmd: str, pc_san: int) -> Tuple[str, str]:
    """
    Check SAN and return result message and color.
    Arguments:
        cmd {str} -- command text
        pc_san {int} -- PC's SAN value

    Returns:
        str -- report message
        str -- color that indicates success or failure
    """
    dice_result = int(random.randint(1, 100))
    is_success = pc_san >= dice_result
    if is_success:
        color = COLOR_SUCCESS
        result_word = "成功"
    else:
        color = COLOR_FAILURE
        result_word = "失敗"

    message = f"{result_word} 【SANチェック】 {dice_result}/{pc_san}"
    cmd_parts = cmd.split()
    if len(cmd_parts) == 2:
        match_result = split_alternative_roll_or_value(cmd_parts[1])
        if match_result:
            san_roll =  match_result[0] if is_success else match_result[1]
            san_damage = sum(eval_roll_or_value(san_roll))
            message += f"\n【減少値】 {san_damage}"
    return message, color


def create_post_message_rolls_result(key: str) -> Tuple[str, str, int]:
    """
    Arguments:
        text {str} -- expect evaluatable text
                   examples: "1D3", "2D6", "2D6+3", "1D8+1D4"
    Returns:
        str -- post message
        str -- message detail
        str -- sum
    """
    str_message = ""
    sum_result = 0
    str_detail = ""
    cnt_ptr = 0
    for match in re.findall(r"\d+[dD]\d+", key):
        str_detail += f"{match}".ljust(80)
        is_plus = True
        if cnt_ptr > 0 and str(key[cnt_ptr - 1: cnt_ptr]) == "-":
            is_plus = False
        cnt_ptr += len(match) + 1
        roll_results = eval_roll_or_value(match)
        dice_sum = sum(roll_results)

        str_detail += ", ".join(map(str, roll_results))
        if is_plus:
            if str_message == "":
                str_message = match
            else:
                str_message += f"+{match}"
            sum_result += dice_sum
            str_detail += " [plus] \n"
        else:
            str_message += f"-{match}"
            sum_result -= dice_sum
            str_detail += " [minus] \n"

    if len(key) > cnt_ptr:
        is_plus = True
        if cnt_ptr > 0 and str(key[cnt_ptr - 1: cnt_ptr]) == "-":
            is_plus = False

        str_calc = key[cnt_ptr:]
        match = re.match(r"(\d+)", str_calc)
        result_now = int(match.group(1))

        if is_plus:
            str_message += f"+{str_calc}"
            sum_result += result_now
            str_detail += f"{result_now}".ljust(80)
            str_detail += f"{result_now} [plus] \n"
        else:
            str_message += f"-{str_calc}"
            sum_result -= result_now
            str_detail += f"{result_now}".ljust(80)
            str_detail += f"{result_now} [minus] \n"

    return str_message, str_detail, sum_result


def analyze_update_command(command: str) -> Tuple[str, str, str]:
    """
    analyze update command and return status name, operator and arg

    Arguments:
        command {str} -- command text

    Returns:
        str -- status_name
        str -- operator
        str -- arg

    Examples:
        "u MP+1" => ("MP", "+", "1")
        "u SAN - 10" => ("SAN", "-", "10")
    """
    result = re.fullmatch(r"(.+)\s+(\S+)\s*(\+|\-|\*|\/)\s*(\d+)$", command)
    if result is None:
        return None
    return result.group(2), result.group(3), result.group(4)


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


def bootstrap(event: dict, _context) -> str:
    logging.info(json.dumps(event))
    random.seed()
    token = os.environ["TOKEN"]
    body = event["body"]
    color = ""
    body_split = body.split("&")
    lst_trigger_status = ["知識", "アイデア", "幸運", "STR", "CON",
        "POW", "DEX", "APP", "SIZ", "INT", "EDU", "HP", "MP"]
    map_alias_trigger = {"こぶし": "こぶし（パンチ）"}
    evt_slack = {}
    for datum in body_split:
        l = datum.split("=")
        evt_slack[l[0]] = l[1]
    user_id = evt_slack["user_id"]

    response_url = urllib.parse.unquote(evt_slack["response_url"])
    logging.info(json.dumps(evt_slack))
    if "subtype" in evt_slack:
        return build_response("subtype event")

    message = urllib.parse.unquote_plus(evt_slack["text"])
    channel_id = urllib.parse.unquote(evt_slack["channel_id"])

    user_url = "https://slack.com/api/users.profile.get"
    payload = {
        "token": os.environ["TOKEN"],
        "user": user_id
    }

    res = requests.get(user_url, params=payload, headers={
                       'Content-Type': 'application/json'})
    data_user = json.loads(res.text)
    print(data_user)
    key = format_as_command(message)
    
    bot = Bot()
    bot.key = key
    bot.dispatch()

    if re.match(r"init.<https://charasheet.vampire-blood.net/.*", message):
        color = COLOR_ATTENTION
        match_url = re.match(r".*<(https.*)>", message)
        param = set_user_params(user_id, match_url.group(1))
        name_display = param["name"] + \
            " - (" + data_user["profile"]["real_name"] + ")"

        name_display = unicodedata.normalize("NFKC", name_display)
        data_user["profile"]["display_name"] = name_display

        post_command("init " + match_url.group(1),
                     token, data_user, channel_id, True)
        param["user_id"] = user_id
        dict_state = get_dict_state(user_id)
        url = "https://slack.com/api/users.profile.set"
        set_params = {'token': token,
                      'user': user_id,
                      'profile': json.dumps(
                      {
                          "display_name": name_display
                      }
                  )
        }
        headers = {'Content-Type': 'application/json'}
        r = requests.get(url, params=set_params, headers=headers)
        print(r.text)

        return_message = get_status_message("INIT CHARA", param, dict_state)
    elif key in ("HELP", "H"):
        post_command(message, token, data_user, channel_id, False)
        return_message = "command list: init, update<u>, status<s>, roll, sanc\n"\
            "more info... https://github.com/cahlchang/CoCNonKP/blob/master/command_reference.md"

    elif key in ("UPDATE", "U"):
        post_command(message, token, data_user, channel_id, False)
        color = COLOR_ATTENTION
        dict_state = get_dict_state(user_id)
        url_from_state = dict_state["url"]
        param = set_user_params(user_id, url_from_state, True)
        return_message = get_status_message("UPDATE", param, dict_state)
    elif re.match("(U+.*|UPDATE+.*)", key):
        color = COLOR_ATTENTION
        result = analyze_update_command(key)
        dict_state = get_dict_state(user_id)
        if result:
            status_name, operator, arg = result
            if status_name in dict_state:
                val_targ = dict_state[status_name]
            else:
                val_targ = "0"

            num_targ = eval(f'{val_targ}{operator}{arg}')
            post_command(f"u {status_name}{operator}{arg}",
                         token, data_user, channel_id)

        dict_state[status_name] = num_targ
        set_state(user_id, dict_state)
        return_message = get_status_message("UPDATE STATUS",
                                            get_user_params(user_id,
                                                            dict_state["pc_id"]),
                                            dict_state)
    elif re.match("KP+.*START", key):
        color = COLOR_ATTENTION
        kp_name = "KP by " + data_user["profile"]["real_name"]
        data_user["profile"]["display_name"] = kp_name
        post_command(f"kp start", token, data_user, channel_id)
        set_start_session(user_id, kp_name)
        return_message = f"セッションを開始します。\n参加コマンド\n```/cc join {user_id}```"
    elif re.match("JOIN+.*", key):
        color = COLOR_ATTENTION
        dict_state = get_dict_state(user_id)
        kp_id = analyze_join_command(key)
        if kp_id:
            post_command(f"join {kp_id}", token, data_user, channel_id)
            add_gamesession_user(kp_id, user_id, dict_state["pc_id"])
            dict_state["kp_id"] = kp_id
            set_state(user_id, dict_state)
            return_message = "参加しました"
        else:
            return_message = f"{message}\nJOINコマンドが不正です"
    elif re.match("KP+.*ORDER.*", key):
        color = COLOR_ATTENTION
        target_status = analyze_kp_order_command(key)
        lst_user_data = get_lst_player_data(user_id, target_status)
        msg = f"{target_status}順\n"
        post_command(f"kp order {target_status}", token, data_user, channel_id)
        cnt = 0
        for user_data in lst_user_data:
            cnt += 1
            name = user_data["name"]
            v = user_data[target_status]
            msg += f"{cnt}, {name} ({v}) \n"
        return_message = msg
    elif "GET" == key:
        return_message = json.dumps(
            get_user_params(user_id), ensure_ascii=False)
        return return_param(response_url, user_id, return_message, color, "ephemeral")
    elif "GETSTATE" == key:
        return_message = json.dumps(
            get_dict_state(user_id), ensure_ascii=False)
    elif message in lst_trigger_param:
        #TODO コマンド設計から考える
        param = get_user_params(user_id, "")
        return_message = "【{}】現在値{}".format(message, param[message])
    elif "景気づけ" == key:
        post_command(f"景気づけ", token, data_user, channel_id)
        num = int(random.randint(1, 100))
        return_message = "景気づけ：{}".format(num)
    elif "素振り" == key:
        post_command(f"素振り", token, data_user, channel_id)
        random.seed()
        num = int(random.randint(1, 100))
        return_message = "素振り：{}".format(num)
    elif "起床ガチャ" == key:
        post_command(f"起床ガチャ", token, data_user, channel_id)
        num = int(random.randint(1, 100))
        return_message = "起床ガチャ：{}".format(num)
    elif "お祈り" == key:
        post_command(f"お祈り", token, data_user, channel_id)
        num = int(random.randint(1, 100))
        return_message = "お祈り：{}".format(num)
    elif "ROLL" == key:
        post_command(f"roll", token, data_user, channel_id)
        num = int(random.randint(1, 100))
        return_message = "1D100：{}".format(num)
    elif "能力値" == key:
        param = get_user_params(user_id)
        return_message = ""
        cnt = 0
        for trigger_param in lst_trigger_param:
            cnt += 1
            return_message += "{}:{} ".format(trigger_param,
                                              param[trigger_param])
            if cnt == 1:
                return_message += "\n"
            elif cnt == 9:
                break
    elif re.match("NAME.*", key):
        post_command(message, token, data_user, channel_id, True)
        return_message = "名前を設定しました"
    elif key in ("ステータス", "STATUS", "S"):
        post_command(message, token, data_user, channel_id)
        param = get_user_params(user_id)
        color = COLOR_ATTENTION
        dict_state = get_dict_state(user_id)
        return_message = get_status_message(
            "STATUS", get_user_params(user_id, dict_state["pc_id"]), dict_state)
    elif key.startswith("SANC"):
        post_command(message, token, data_user, channel_id)
        param = get_user_params(user_id)
        c_san = int(param["現在SAN"])
        dict_state = get_dict_state(user_id)
        if "SAN" in dict_state:
            d_san = int(dict_state["SAN"])
        else:
            d_san = 0
        sum_san = c_san + d_san

        return_message, color = get_sanc_result(key, sum_san)

    elif re.match(r"HIDE.*", key):
        return_message = ""
        post_command(f"hide ？？？", token, data_user, channel_id)

        text = "結果は公開されず、KPが描写だけ行います"
        return_message = "【シークレットダイス】？？？"

        payload = {
            'token': token,
            "response_type": "in_channel",
            'text': text,
            "attachments": json.dumps([
                {
                    "text": return_message,
                    "type": "mrkdwn",
                    "color": color
                }
            ])
        }

        res = requests.post(response_url,
                            data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'})
        print(res.text)

        def post_hide(user_id):
            post_url = 'https://slack.com/api/chat.postMessage'
            param = get_user_params(user_id)
            dict_state = get_dict_state(user_id)
            channel = '@' + dict_state["kp_id"]
            color_hide = "gray"

            m = re.match(r"HIDE\s(.*?)(\+|\-|\*|\/)?(\d{,})?$", key)
            if m is None:
                text = "role not found"
                post_message = f"技能名が解釈できません。\n{key}"
            elif m.group(1) and m.group(1) not in param:
                text = "role miss"
                name_role = m.group(1)
                post_message = f"この技能は所持していません。\n{key}"
            else:
                name_role = m.group(1)
                n_targ = 0
                msg_rev = "+0"
                if type(param[name_role]) == list:
                    n_targ = int(param[name_role][5])
                else:
                    n_targ = int(param[name_role])

                msg_disp = n_targ

                if name_role in dict_state:
                    n_targ += dict_state[name_role]
                if m.group(2) is not None:
                    if m.group(2) == "+":
                        n_targ += int(m.group(3))
                        msg_rev = "+" + str(m.group(3))
                    elif m.group(2) == "-":
                        n_targ -= int(m.group(3))
                        msg_rev = "-" + str(m.group(3))
                    elif m.group(2) == "*":
                        n_targ *= int(m.group(3))
                        msg_rev = "*" + str(m.group(3))
                    elif m.group(2) == "/":
                        n_targ /= int(m.group(3))
                        msg_rev = "/" + str(m.group(3))

                num = int(random.randint(1, 100))

                str_result, color_hide = judge_1d100(int(n_targ), num)
                post_message = f"{str_result} 【{name_role}】 {num}/{n_targ} ({msg_disp}{msg_rev})"

                text = f"<@{user_id}> try {name_role}"

            payload = {
                'token': token,
                'channel': channel,
                'text': text,
                "attachments": json.dumps([
                    {
                        "text": post_message,
                        "type": "mrkdwn",
                        "color": color_hide
                    }
                ])
            }

            res = requests.post(post_url, data=payload)
            logging.info(f"post to Slack. response:[{res}]")
        with futures.ThreadPoolExecutor() as executor:
            future_hide = executor.submit(post_hide, user_id)
            future_hide.result()

        return ""
    elif re.match(r"^\d+[dD]\d*.*", key):
        str_message, str_detail, sum_result = create_post_message_rolls_result(key)

        post_command(str_message, token, data_user, channel_id)

        color = "#4169e1"
        return_message = f"*{sum_result}* 【ROLLED】\n {str_detail}"
    else:
        logging.info("command start")
        param = get_user_params(user_id)
        # todo spaceが入っていてもなんとかしたい
        message = urllib.parse.unquote(message)
        post_command(message, token, data_user, channel_id)

        if not 0 == len(list(filter(lambda matcher: re.match(message, matcher, re.IGNORECASE), map_alias_trigger.keys()))):
            message = map_alias_trigger[message.upper()]

        proc = r"^(.*)(\+|\-|\*|\/)(\d+)$"

        result_parse = re.match(proc, message)
        is_correction = False
        msg_correction = "+0"
        if result_parse:
            message = result_parse.group(1)
            key = message.upper()
            operant = result_parse.group(2)
            args = result_parse.group(3)
            msg_correction = operant + args
            is_correction = True

        if 0 == len(list(filter(lambda matcher: re.match(message, matcher, re.IGNORECASE), param.keys()))):
            return build_response("@{} norm message".format(user_id))

#        if message not in param:
#            return_param(response_url, user_id, "解釈出来ないコマンドです", color, "ephemeral")

        data = param[message]

        num = int(random.randint(1, 100))
        msg_eval2 = message.upper()
        if msg_eval2 in lst_trigger_status or "現在SAN" == message:
            num_targ = data
        else:
            num_targ = data[-1]

        msg_num_targ = num_targ
        if is_correction:
            num_targ = eval('{}{}{}'.format(num_targ, operant, args))
            num_targ = math.ceil(num_targ)

        str_result, color = judge_1d100(int(num_targ), num)
        return_message = f"{str_result} 【{message}】 {num}/{num_targ} ({msg_num_targ}{msg_correction})"
        logging.info("command end")

    return return_param(response_url, user_id, return_message, color)


def lambda_handler(event: dict, _context) -> str:
    try:
        return bootstrap(event, _context)
    except Exception as e:
        token = os.environ["TOKEN"]
        command_url = "https://slack.com/api/chat.postMessage?"
        channel_id = 'CNCM21Z9T'
        payload = {
            "token": token,
            "channel": channel_id,
            "text": traceback.format_exc()
        }
        print(payload)
        res = requests.get(command_url, params=payload)
