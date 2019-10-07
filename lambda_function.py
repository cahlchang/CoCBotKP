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
STATE_FILE_PATH = "./state.json"

lst_trigger_param = ["name","STR","CON","POW","DEX","APP","SIZ","INT","EDU","HP","MP","初期SAN","現在SAN","アイデア","幸運","知識"]
lst_trigger_role = ["応急手当", "鍵開け", "隠す" , "隠れる", "聞き耳", "忍び歩き","写真術", "精神分析", "追跡", "登攀", "図書館", "目星", "運転", "機械修理", "重機械操作", "乗馬", "水泳", "製作.*?", "操縦.*?", "跳躍","電気修理", "ナビゲート", "変装", "言いくるめ", "信用", "説得", "値切り",  "母国語.*?", "医学", "オカルト", "化学", "クトゥルフ神話", "芸術.*?", "経理", "考古学", "コンピューター", "心理学", "人類学",  "生物学", "地質学", "電子工学",  "天文学",  "博物学","物理学", "法律", "薬学", "歴史", "製作.*?"]
lst_trigger_action = ["回避", "キック", "組み付き", "こぶし（パンチ）", "頭突き", "投擲", "マーシャルアーツ", "拳銃", "サブマシンガン", "ショットガン", "マシンガン", "ライフル"]

def build_response(message):
    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "body": json.dumps({
            "icon_emoji": "books",
            "text": "未対応のメッセージです。/coc helpで確認ください。"
        })
    }

def get_user_params(user_id, url = None):
    key = user_id + "/test_npc"
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
    
    obj = bucket.Object(key)
    response = obj.get()
    body = response['Body'].read()
    return body.decode('utf-8')
    
def get_url_with_state(user_id):
    key_state = user_id + STATE_FILE_PATH
    
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
    
    obj = bucket.Object(key_state)
    response = obj.get()
    body = response['Body'].read()
    data = json.loads(body.decode('utf-8'))
    print(data)

    return data["url"]
    
def set_user_params(user_id, url, is_update=False):
    logging.info("request start")

    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = res.read().decode('utf-8')
    logging.info("request end")

    name = ''
    dict_param = {}
    is_param_end = False
    is_param_parse = False
    is_param_now_parse = False
    lst_param = []
    
    is_role_end = False
    is_role_parse = False
    is_role_now_parse = False
    role_now_parse = ""
    lst_role = ["応急手当", "鍵開け", "隠す" , "隠れる", "聞き耳", "忍び歩き","写真術", "精神分析", "追跡", "登攀", "図書館", "目星", "運転", "機械修理", "重機械操作", "乗馬", "水泳", "製作.*?", "操縦.*?", "跳躍","電気修理", "ナビゲート", "変装", "言いくるめ", "信用", "説得", "値切り",  "母国語.*?", "医学", "オカルト", "化学", "クトゥルフ神話", "芸術.*?", "経理", "考古学", "コンピューター", "心理学", "人類学",  "生物学", "地質学", "電子工学",  "天文学",  "博物学","物理学", "法律", "薬学", "歴史", "製作.*?"]
    dict_role = {}
    
    is_action_end = False
    is_action_parse = False
    is_action_now_parse = False
    action_now_parse = ""
    lst_action = ["回避", "キック", "組み付き", "こぶし.*", "頭突き", "投擲", "マーシャルアーツ", "拳銃", "サブマシンガン", "ショットガン", "マシンガン", "ライフル"]
    dict_action = {}
    
    logging.info("regexp start")
    lst = body.splitlines()
    c0 = 0
    c1 = 0
    c2 = 0
    c3 = 0
    
    for line in lst:
    
        if False == is_param_end:
            if re.match('.*<div class="disp"><table class="pc_making">.*', line):
                is_param_parse = True

            if is_param_parse:
                if re.match('.*<th colspan="2">現在値</th>.*', line):
                    is_param_now_parse = True
            if is_param_now_parse:
                if re.match('/*</tr>.*', line):
                    lst = ["STR","CON","POW","DEX","APP","SIZ","INT","EDU","HP","MP","初期SAN","アイデア","幸運","知識"]
                    lst_tmp = []
                    for raw_param in lst_param:
                        m = re.match('.*value="(.*?)".*', raw_param)
                        if m: lst_tmp.append(m.group(1))
                        
                    for name_param in lst:
                        dict_param[name_param] = lst_tmp.pop(0)
                    is_param_end = True
                    c2 += 1
                    logging.info("param end")

                lst_param.append(line)
            continue
        
        if re.match(".*SAN_Left.*", line):
            is_param_end = True
            m = re.match('.*value="(.*?)".*', line)
            dict_param["現在SAN"] = m.group(1)
            logging.info("san end")
            continue
            
        if False == is_action_end:
            if is_action_now_parse:
                if not action_now_parse in dict_action:
                    dict_action[action_now_parse] = []
                    
                m = re.match('.*value="(.*?)".*', line)
                if m:
                    dict_action[action_now_parse].append(m.group(1))
                else:
                    dict_action[action_now_parse].append(0)

            m = re.match('.*TBAP.*', line)
            if m:
                is_action_now_parse = False
                role_now_parse = ""
                c1 += 1

            for action in lst_action:
                m = re.match('.*<th>({})<\/th>.*'.format(action), line)
                if m:
                    is_action_now_parse = True
                    action_now_parse = m.group(1)
            
            m = re.match('.*btnDelLineBattleArts.*', line)
            if m:
                is_action_end = True
            continue

        if False == is_role_end:
            if is_role_now_parse:
                if not role_now_parse in dict_param:
                    dict_param[role_now_parse] = []
                m = re.match('.*value="(.*?)".*', line)
                if m:
                    dict_param[role_now_parse].append(m.group(1))
                else:
                    dict_param[role_now_parse].append(0)
    
            m = re.match('.*(TFAP|TAAP|TCAP|TKAP).*', line) 
            if m:
                is_role_now_parse = False
                role_now_parse = ""
                c0 += 1

            for role in lst_role:
                m = re.match('.*<th>({})<\/th>.*'.format(role), line)
                if m:
                    is_role_now_parse = True
                    role_now_parse = m.group(1)
            
            m = re.match('.*btnDelLineKnowArts.*', line)
            if m:
                is_role_end = True
            continue

        if '' == name:
            m_name = re.match('.*<input name="pc_name" class="str" id="pc_name" size="55" type="text" value="(.*)">.*', line)
            if m_name:
                name = m_name.group(1)
            continue
        

    logging.info(f"c0 {c0}")
    logging.info(f"c1 {c1}")
    logging.info(f"c2 {c2}")
    logging.info(f"c3 {c3}")
    dict_param.update(dict_role)
    dict_param.update(dict_action)
    dict_param["name"] = name

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
    
    logging.info("puts3 start")
    key = user_id + "/test_npc"
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
        "url": url
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

def lambda_handler(event: dict, context) -> str:
    logging.info(json.dumps(event))
    body = event["body"]
    color = ""
    body_split = body.split("&")
    lst_trigger_status = ["知識", "アイデア", "幸運", "STR","CON","POW","DEX","APP","SIZ","INT","EDU","HP","MP"]
    map_alias_trigger = {"こぶし": "こぶし（パンチ）"}
    evt_slack = {}
    for datum in body_split:
        l = datum.split("=")
        evt_slack[l[0]] = l[1]
    user_id = evt_slack["user_id"]
    logging.info(json.dumps(evt_slack))

    if "subtype" in evt_slack:
        return build_response("subtype event")

    url = "https://slack.com/api/chat.postMessage"
    channel = evt_slack["channel_id"]
    message = urllib.parse.unquote(evt_slack["text"])
    print(message)

    is_trigger_roll = False
    
    lst_trigger = lst_trigger_role + lst_trigger_status + lst_trigger_action + list(map_alias_trigger.keys())
    for datum in lst_trigger:
        msg_eval = message.upper()
        datum = datum.upper()
        if not -1 == msg_eval.find(datum):
            print(datum)
            is_trigger_roll = True

    if re.match("set.<https:\/\/charasheet\.vampire-blood\.net\/.*" , message):
        logging.info("setting start")

        match_url  = re.match(".*(https?://[\w/:%#\$&\?\(\)~\.=\+\-]+)", message)
        return_message = set_user_params(user_id, match_url.group(1))
    elif "update" == message or "u" == message:
        color = "#80D2DE"
        url_from_state = get_url_with_state(user_id)
        param = set_user_params(user_id, url_from_state, True)
        return_message = "【{}】UPDATED\nHP {}/{}　　MP {}/{}　　DEX {}　　SAN{}/{}".format(param["name"], param["HP"],param["HP"],param["MP"],param["MP"],param["DEX"],param["現在SAN"],param["初期SAN"])
    elif "get" == message:
        #match_url  = re.match(".*(https?://[\w/:%#\$&\?\(\)~\.=\+\-]+)", _message)
        return_message = get_user_params(user_id)
    elif is_trigger_roll:
        param = json.loads(get_user_params(user_id, ""))
        #todo spaceが入っていてもなんとかしたい
        message = urllib.parse.unquote(message)
        print(message)
        if message in map_alias_trigger.keys():
            message = map_alias_trigger[message]
        
        proc = "^(.*)(\+|\-|\*|\/)(.*)$"
        result_parse = re.match(proc, message)
        is_correction = False
        msg_correction = "+0"
        if result_parse:
            message = result_parse.group(1)
            operant = result_parse.group(2)
            args = result_parse.group(3)
            msg_correction = operant + args
            is_correction = True
        
        key = message.upper()
        data = param[key]
        
        print(data)
        num = int(random.randint(1,100))
        msg_eval2 = message.upper()
        if msg_eval2 in lst_trigger_status:
            num_targ = data
        else:
            num_targ = data[-1]
        
        msg_num_targ = num_targ
        if is_correction:
            num_targ = eval('{}{}{}'.format(num_targ, operant, args))
            num_targ = math.ceil(num_targ)
            
        print(data)
        str_result = ""
        if 0 <= int(num_targ) - num :
            color = "#36a64f"
            str_result = "成功"
            if 0 >= num - 5:
                color = "#EBB424"
        else:
            color = "#E01E5A"
            str_result = "失敗"
            if 0 <= num - 96:
                color = "#3F0F3F"

        return_message = "{} 【{}】 {}/{} ({}{})".format(str_result, message, num, num_targ, msg_num_targ, msg_correction)
    elif message in lst_trigger_param:
        param = json.loads(get_user_params(user_id, ""))
        return_message = "【{}】現在値{}".format(message, param[message])
    elif "景気づけ" == message:
        num = int(random.randint(1,100))
        return_message = "景気づけ：{}".format(num)
    elif "素振り" == message:
        num = int(random.randint(1,100))
        return_message = "素振り：{}".format(num)
    elif "起床ガチャ" == message:
        num = int(random.randint(1,100))
        return_message = "起床ガチャ：{}".format(num)
    elif "お祈り" == message:
        num = int(random.randint(1,100))
        return_message = "お祈り：{}".format(num)
    elif "roll" == message:
        num = int(random.randint(1,100))
        return_message = "1D100：{}".format(num)
    elif "能力値" == message:
        param = json.loads(get_user_params(user_id, ""))
        return_message = ""
        cnt = 0
        for p in lst_trigger_param:
            cnt += 1
            return_message += "{}:{} ".format(p, param[p])
            if cnt == 1:
                return_message += "\n"
            elif cnt == 9:
                break
    elif "pcname" == message:
        pass
    elif "ステータス" == message or "status" == message or "s" == message:
        param = json.loads(get_user_params(user_id, ""))
        color = "#80D2DE"
        return_message = "【{}】\nHP {}/{}　　MP {}/{}　　DEX {}　　SAN{}/{}".format(param["name"], param["HP"],param["HP"],param["MP"],param["MP"],param["DEX"],param["現在SAN"],param["初期SAN"])

    else:
        return build_response("@{} norm message".format(user_id))

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
                    "color": color
                }
            ]
        })
