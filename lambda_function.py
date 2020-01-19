"""
Slack Bot function for CoC TRPG.
This is deployed on AWS Lambda

[terms]
state: PC's HP, MP, SAN, キャラクター保管庫URL, etc...
"""

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

import boto3
import requests

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


def set_start_session(user_id):
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

    logging.info("puts3 end")
    if is_update:
        return dict_param

    key_state = user_id + STATE_FILE_PATH
    dict_state = {
        "url": url,
        "pc_id": dict_param["pc_id"]
    }
    logging.info("puts3 2 start")
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


def judge_1d100(target: int, actual: int):
    """"
    Judge 1d100 dice result, and return text and color for message.
    Result is critical, success, failure or fumble.
    Arguments:
        target {int} -- target value (ex. skill value)
        actual {int} -- dice value
    Returns:
        message {string}
        rgb_color {string}
    """
    if actual <= 5:
        return "成功", COLOR_CRITICAL
    elif actual <= target:
        return "成功", COLOR_SUCCESS
    elif actual >= 96:
        return "失敗", COLOR_FUMBLE
    return "失敗", COLOR_FAILURE

def split_alternative_roll_or_value(cmd) -> bool:
    """
    Split text 2 roll or value.
    Alternative roll is like following.
    - 0/1
    - 1/1D3
    - 1D20/1D100

    Arguments:
        cmd {str} -- command made by upper case
    Returns:
        tuple of 2 int or None
    """
    element_matcher = r"(\d+D?\d*)"
    result = re.fullmatch(f"{element_matcher}/{element_matcher}", cmd)
    if result is None or len(result.groups()) != 2:
        return None
    return result.groups()


def lambda_handler(event: dict, _context) -> str:
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

    message = urllib.parse.unquote(evt_slack["text"])
    channel_id = urllib.parse.unquote(evt_slack["channel_id"])

    user_url = "https://slack.com/api/users.profile.get"
    payload = {
        "token": token,
        "user": user_id
    }

    res = requests.get(user_url, params=payload, headers={
                       'Content-Type': 'application/json'})
    data_user = json.loads(res.text)
    print(data_user)

    key = message.upper()

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
        proc = r"^(.*?)\+(.*?)(\+|\-|\*|\/)(.*)$"
        r = re.match(proc, message)
        dict_state = get_dict_state(user_id)
        if r:
            message = r.group(2)
            key = message.upper()
            operant = r.group(3)
            args = r.group(4)
            if key in dict_state:
                val_targ = dict_state[key]
            else:
                val_targ = "0"

            num_targ = eval('{}{}{}'.format(val_targ, operant, args))
            post_command(f"u {key}{operant}{args}",
                         token, data_user, channel_id)

        dict_state[key] = num_targ
        set_state(user_id, dict_state)
        return_message = get_status_message("UPDATE STATUS",
                                            get_user_params(user_id,
                                                            dict_state["pc_id"]),
                                            dict_state)
    elif re.match("KP+.*START", key):
        color = COLOR_ATTENTION
        post_command(f"kp start", token, data_user, channel_id)
        set_start_session(user_id)
        return_message = f"セッションを開始します。\n参加コマンド\n```/cc join {user_id}```"
    elif re.match("JOIN+.*", key):
        color = COLOR_ATTENTION
        proc = r"^(.*)\+(.*)$"
        dict_state = get_dict_state(user_id)
        result_parse = re.match(proc, message)
        kp_id = ""
        if result_parse:
            kp_id = result_parse.group(2)
        post_command(f"join {kp_id}", token, data_user, channel_id)

        add_gamesession_user(kp_id, user_id, dict_state["pc_id"])
        dict_state["kp_id"] = kp_id
        set_state(user_id, dict_state)
        return_message = "参加しました"
    elif re.match("KP+.*ORDER.*", key):
        color = COLOR_ATTENTION
        proc = r"KP\+ORDER\+(.*)"
        m = re.match(proc, key)
        targ_roll = m.group(1)
        lst_user_data = get_lst_player_data(user_id, targ_roll)
        msg = f"{targ_roll}順\n"
        post_command(f"kp order {targ_roll}", token, data_user, channel_id)
        cnt = 0
        for user_data in lst_user_data:
            cnt += 1
            name = user_data["name"]
            v = user_data[targ_roll]
            msg += f"{cnt}, {name} ({v}) \n"
        return_message = msg
    # elif "list"  == message:
    #     #TODO 自分のキャラクタ一覧をリスト表示する
    # elif "kp add npc" == message:
    #     #TODO NPCのキャラシを追加できるようにしたい
    elif "GET" == key:
        return_message = json.dumps(
            get_user_params(user_id), ensure_ascii=False)
        return return_param(response_url, user_id, return_message, color, "ephemeral")
    elif "GETSTATE" == key:
        return_message = json.dumps(
            get_dict_state(user_id), ensure_ascii=False)
    elif message in lst_trigger_param:
        # TODO コマンド設計から考える
        param = get_user_params(user_id, "")
        return_message = "【{}】現在値{}".format(message, param[message])
    elif "景気づけ" == key:
        post_command(f"景気づけ", token, data_user, channel_id)
        num = int(random.randint(1, 100))
        return_message = "景気づけ：{}".format(num)
    elif "素振り" == key:
        post_command(f"素振り", token, data_user, channel_id)
        # TODO なんかシード値をなんかしたい（Lambdaなので意味はない）
        random.seed()
        num = int(random.randint(1, 100))
        return_message = "素振り：{}".format(num)
    elif "起床ガチャ" == key:
        post_command(f"起床ガチャ", token, data_user, channel_id)
        # TODO 現在時刻と合わせて少し変化を入れたい
        num = int(random.randint(1, 100))
        return_message = "起床ガチャ：{}".format(num)
    elif "お祈り" == key:
        post_command(f"お祈り", token, data_user, channel_id)
        # TODO たまに変な効果を出すようにしたい
        num = int(random.randint(1, 100))
        return_message = "お祈り：{}".format(num)
    elif "ROLL" == key:
        post_command(f"roll", token, data_user, channel_id)
        # TODO 1d100だけじゃなく、ダイス形式対応
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
    elif "SANC" == key:
        post_command(message, token, data_user, channel_id)
        param = get_user_params(user_id)
        c_san = int(param["現在SAN"])
        dict_state = get_dict_state(user_id)
        if "SAN" in dict_state:
            d_san = int(dict_state["SAN"])
        else:
            d_san = 0
        sum_san = c_san + d_san

        num_targ = int(random.randint(1, 100))
        if sum_san >= num_targ:
            color = COLOR_SUCCESS
            str_result = "成功"
        else:
            color = COLOR_FAILURE
            str_result = "失敗"

        return_message = f"{str_result} 【SANチェック】 {num_targ}/{sum_san}"
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

            m = re.match(r"HIDE\+(.*?)(\+|\-|\*|\/)?(\d{,})?$", key)
            if m is None:
                post_message = "技能名が解釈できません"
            elif m.group(1) and m.group(1) not in param:
                name_role = m.group(1)
                post_message = "この技能は所持していません"
                color_hide = "gray"
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
        str_message = ""
        sum_result = 0
        str_detail = ""
        cnt_ptr = 0
        for match in re.findall(r"\d+[dD]\d+", key):
            str_detail += f"{match}\t".ljust(80)
            is_plus = True
            if cnt_ptr > 0 and str(key[cnt_ptr - 1: cnt_ptr]) == "-":
                is_plus = False
            cnt_ptr += len(match) + 1
            match_roll = re.match(r"(\d+)(d|D)(\d+).*", match)
            print(match)
            print(match_roll.group(1))
            result_now = 0
            lst = []
            n_tmp = 0
            # TODO: ループの仕方を見直す
            for _i in range(0, int(match_roll.group(1))):
                result_now = random.randint(1, int(match_roll.group(3)))
                n_tmp += result_now
                lst.append(str(result_now))

            str_detail += ", ".join(lst)
            if is_plus:
                if str_message == "":
                    str_message = match
                else:
                    str_message += f"+{match}"
                sum_result += n_tmp
                str_detail += " [plus] \n"
            else:
                str_message += f"-{match}"
                sum_result -= n_tmp
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
                str_detail += f"{result_now}".ljust(83)
                str_detail += f"{result_now} [plus] \n"
            else:
                str_message += f"-{str_calc}"
                sum_result -= result_now
                str_detail += f"{result_now}".ljust(83)
                str_detail += f"{result_now} [minus] \n"

        post_command(str_message, token, data_user, channel_id)

        color = "#4169e1"
        return_message = f"*{sum_result}* 【ROLLED】\n {str_detail}"
    else:
        logging.info("command start")
        param = get_user_params(user_id)
        # todo spaceが入っていてもなんとかしたい
        message = urllib.parse.unquote(message)
        post_command(message, token, data_user, channel_id)

        # todo
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

        # todo
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
            # todo dont use eval
            num_targ = eval('{}{}{}'.format(num_targ, operant, args))
            num_targ = math.ceil(num_targ)

        str_result, color = judge_1d100(int(num_targ), num)

        return_message = f"{str_result} 【{message}】 {num}/{num_targ} ({msg_num_targ}{msg_correction})"
        logging.info("command end")

    return return_param(response_url, user_id, return_message, color)
