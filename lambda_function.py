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
# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

AWS_S3_BUCKET_NAME = 'wheellab-coc-pcparams'
STATE_FILE_PATH = "/state.json"

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
    """
    get_user_params function is PC parameter from AWS S3
    """
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
    """
    set_state function is update PC state param.
    """
    key_state = user_id + STATE_FILE_PATH

    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(AWS_S3_BUCKET_NAME)

    obj_state = bucket.Object(key_state)
    body_state = json.dumps(dict_state, ensure_ascii=False)
    obj_state.put(
        Body=body_state.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )


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
            san_roll = match_result[0] if is_success else match_result[1]
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

def bootstrap(event: dict, _context) -> str:
    logging.info(json.dumps(event))
    bot = Bot()
    if "params" in event and "path" in event["params"]:
        bot.install_bot(event)
        # todo redirectでワークスペースに飛ぶように
        return "ok"
    random.seed()
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
    team_id = urllib.parse.unquote(evt_slack["team_id"])

    token = bot.get_token(team_id)
    user_url = "https://slack.com/api/users.profile.get"
    payload = { "token": token,
                "user": user_id}

    res = requests.get(user_url, params=payload, headers={
        'Content-Type': 'application/json'})
    data_user = json.loads(res.text)
    print(data_user)
    key = format_as_command(message)

    bot.init_param(user_id,
                   response_url,
                   key,
                   message,
                   data_user,
                   channel_id,
                   team_id)

    is_bot_command = bot.dispatch()

    if is_bot_command:
        return None
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
    elif key in ("ステータス", "STATUS", "S"):
        post_command(message, token, data_user, channel_id)
        param = get_user_params(user_id)
        color = COLOR_ATTENTION
        dict_state = get_dict_state(user_id)
        return_message = get_status_message(
            "STATUS", get_user_params(user_id, dict_state["pc_id"]), dict_state)
    elif "GET" == key:
        return_message = json.dumps(
            get_user_params(user_id), ensure_ascii=False)
        return return_param(response_url, user_id, return_message, color, "ephemeral")
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
        # 一回のコマンドで複数回呼ばれてる？いつか直す
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
        channel_id = 'CNCM21Z9T'
        payload = {
            "token": os.environ["WS_TOKEN"],
            "channel": channel_id,
            "text": traceback.format_exc()
        }
        res = requests.get("https://slack.com/api/chat.postMessage?",
                           params=payload)
        print(res.text)
