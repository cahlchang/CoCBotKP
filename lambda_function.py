# -*- coding: utf-8 -*-
import os
import json
import logging
import urllib.request
import boto3
import re
import random
import urllib.parse
import math

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_S3_BUCKET_NAME = 'wheellab-coc-pcparams'
STATE_FILE_PATH = "/state.json"
KP_FILE_PATH = "/kp.json"

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


def get_user_params(user_id, pc_id = None):
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
                    lst = ["STR", "CON", "POW", "DEX", "APP", "SIZ", "INT", "EDU", "HP", "MP", "初期SAN", "アイデア", "幸運", "知識"]
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
            m = re.match('.*<input name="pc_name" class="str" id="pc_name" size="55" type="text" value="(.*)">.*', line)
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
        "Name\[\]": "{}"
    }
    for key in dict_param.keys():
        for proc, key_new in dict_replace.items():
            m = re.match('.*{}.*'.format(proc), key)
            if m:
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

    logging.info("puts3 2 end")
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


def lambda_handler(event: dict, context) -> str:
    logging.info(json.dumps(event))
    random.seed()
    body = event["body"]
    color = ""
    body_split = body.split("&")
    # TODO トリガーはjsonファイルから取り出す
    lst_trigger_status = ["知識", "アイデア", "幸運", "STR", "CON", "POW", "DEX", "APP", "SIZ", "INT", "EDU", "HP", "MP"]
    map_alias_trigger = {"こぶし": "こぶし（パンチ）"}
    evt_slack = {}
    for datum in body_split:
        l = datum.split("=")
        evt_slack[l[0]] = l[1]
    user_id = evt_slack["user_id"]
    logging.info(json.dumps(evt_slack))

    if "subtype" in evt_slack:
        return build_response("subtype event")

    message = urllib.parse.unquote(evt_slack["text"])
    key = message.upper()

    if re.match(r"init.<https://charasheet.vampire-blood.net/.*", message):
        color = "#80D2DE"
        match_url  = re.match(".*(https?://[\w/:%#\$&\?\(\)~\.=\+\-]+)", message)
        param = set_user_params(user_id, match_url.group(1))
        logging.info("set params")
        return_message = "【{}】SET\nHP {}/{}　　MP {}/{}　　DEX {}　　SAN{}/{}".format(param["name"], param["HP"],param["HP"],param["MP"],param["MP"],param["DEX"],param["現在SAN"],param["初期SAN"])
    elif "UPDATE" == key or "U" == key:
        color = "#80D2DE"
        url_from_state = get_url_with_state(user_id)
        param = set_user_params(user_id, url_from_state, True)
        return_message = "【{}】UPDATED\nHP {}/{}　　MP {}/{}　　DEX {}　　SAN{}/{}".format(param["name"], param["HP"],param["HP"],param["MP"],param["MP"],param["DEX"],param["現在SAN"],param["初期SAN"])
    elif "update TODO" == message:
        #TODO stateファイルに差分を書く
        PASS
    elif "list"  == message:
        PASS
        #TODO 自分のキャラクタ一覧をリスト表示する
    elif "START" == key:
        color = "#80D2DE"
        set_start_session(user_id)
        return_message = f"セッションを開始します。\n参加コマンド\n```/cc join {user_id}```"
    elif re.match("JOIN+.*", key):
        color = "#80D2DE"
        proc = r"^(.*)+(.*)$"
        dict_state = get_dict_state(user_id)
        result_parse = re.match(proc, message)
        kp_id = ""
        if result_parse:
            kp_id = result_parse.group(2)

        add_gamesession_user(kp_id, user_id, dict_state["pc_id"])

        return_message = "こんなコマンド"
    elif re.match("KP+.*ORDER.*" , key):
        color = "#80D2DE"
        proc = "^(.*)\+ORDER\+(.*)$"
        m = re.match(proc, key)
        targ_roll = m.group(2)
        lst_user_data = get_lst_player_data(user_id, targ_roll)
        msg = f"{targ_roll}順\n"
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
        return_message = get_user_params(user_id)
    elif message in lst_trigger_param:
        #TODO コマンド設計から考える
        param = json.loads(get_user_params(user_id, ""))
        return_message = "【{}】現在値{}".format(message, param[message])
    elif "景気づけ" == key:
        num = int(random.randint(1,100))
        return_message = "景気づけ：{}".format(num)
    elif "素振り" == key:
        #TODO なんかシード値をなんかしたい（Lambdaなので意味はない）
        random.seed()
        num = int(random.randint(1,100))
        return_message = "素振り：{}".format(num)
    elif "起床ガチャ" == key:
        # TODO 現在時刻と合わせて少し変化を入れたい
        num = int(random.randint(1,100))
        return_message = "起床ガチャ：{}".format(num)
    elif "お祈り" == key:
        # TODO たまに変な効果を出すようにしたい
        num = int(random.randint(1,100))
        return_message = "お祈り：{}".format(num)
    elif "roll" == key:
        #TODO 1d100だけじゃなく、ダイス形式対応
        num = int(random.randint(1,100))
        return_message = "1D100：{}".format(num)
    elif "能力値" == key:
        param = json.loads(get_user_params(user_id, ""))
        return_message = ""
        cnt = 0
        for trigger_param in lst_trigger_param:
            cnt += 1
            return_message += "{}:{} ".format(trigger_param, param[trigger_param])
            if cnt == 1:
                return_message += "\n"
            elif cnt == 9:
                break
    elif "pcname" == message:
        pass
    elif key in ("ステータス", "STATUS", "S"):
        param = get_user_params(user_id)
        color = "#80D2DE"
        dict_state = get_dict_state(user_id)
        return_message = get_status_message("STATUS", get_user_params(user_id, dict_state["pc_id"]), dict_state)
    elif "SANC" == key:
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
            color = "#36a64f"
            str_result = "成功"
        else:
            color = "#E01E5A"
            str_result = "失敗"

        return_message = f"{str_result} 【SANチェック】 {num_targ}/{sum_san}"
    else:
        logging.info("command start")
        param = get_user_params(user_id)
        # todo spaceが入っていてもなんとかしたい
        message = urllib.parse.unquote(message)

        if not 0 == len(list(filter(lambda matcher: re.match(message , matcher, re.IGNORECASE), map_alias_trigger.keys()))):
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

        if 0 == len(list(filter(lambda matcher: re.match(message , matcher, re.IGNORECASE), param.keys()))):
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

        str_result = ""
        if 0 <= int(num_targ) - num:
            color = "#36a64f"
            str_result = "成功"
            if 0 >= num - 5:
                color = "#EBB424"
        else:
            color = "#E01E5A"
            str_result = "失敗"
            if 0 <= num - 96:
                color = "#3F0F3F"

        return_message = f"{str_result} 【{message}】 {num}/{num_targ} ({msg_num_targ}{msg_correction})"
        logging.info("command end")

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "body": json.dumps({
            "icon_emoji": "books",
            "response_type": "in_channel",
            "text": "<@{}>".format(user_id),
            "attachments": [
                {
                    "text": return_message,
                    "type": "mrkdwn",
                    "color": color
                }
            ]
        })
    }
