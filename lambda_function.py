# -*- coding: utf-8 -*-
import os
import json
import logging
import urllib.request
import boto3
import re
import random
import urllib.parse

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_S3_BUCKET_NAME = 'wheellab-coc-pcparams'

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
    
def set_user_params(user_id, url):
    key = user_id + "/test_npc"
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(AWS_S3_BUCKET_NAME)
    obj = bucket.Object(key)
    
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as res:
        body = res.read().decode('utf-8')

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
    
    for line in body.splitlines():
        if '' == name:
            m_name = re.match('.*<input name="pc_name" class="str" id="pc_name" size="55" type="text" value="(.*)">.*', line)
            if m_name:
                name = m_name.group(1)
    
        if False == is_role_end:
            if is_role_now_parse:
                if not role_now_parse in dict_param:
                    dict_param[role_now_parse] = []
                m = re.match('.*value="(.*?)".*', line)
                if m:
                    dict_param[role_now_parse].append(m.group(1))
                else:
                    dict_param[role_now_parse].append(0)
    
            m = re.match('.*sumTD.*', line) 
            if m:
                is_role_now_parse = False
                role_now_parse = ""
    
            for role in lst_role:
                m = re.match('.*<th>({})<\/th>.*'.format(role), line)
                if m:
                    is_role_now_parse = True
                    role_now_parse = m.group(1)
                    
        if False == is_action_end:
            if is_action_now_parse:
                print("aaa")
                
                if not action_now_parse in dict_action:
                    dict_action[action_now_parse] = []
                    
                m = re.match('.*value="(.*?)".*', line)
                if m:
                    dict_action[action_now_parse].append(m.group(1))
                else:
                    dict_action[action_now_parse].append(0)

            m = re.match('.*sumTD.*', line)
            if m:
                is_action_now_parse = False
                role_now_parse = ""

            for action in lst_action:
                m = re.match('.*<th>({})<\/th>.*'.format(action), line)
                if m:
                    is_action_now_parse = True
                    action_now_parse = m.group(1)
                
        
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
    
                lst_param.append(line)
        
        if re.match(".*SAN_Left.*", line):
            m = re.match('.*value="(.*?)".*', line)
            dict_param["現在SAN"] = m.group(1)

    dict_param.update(dict_role)
    dict_param.update(dict_action)
    dict_param["name"] = name

    body = json.dumps(dict_param, ensure_ascii=False)

    response = obj.put(
        Body=body.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )
    
    return "setting"

def lambda_handler(event: dict, context) -> str:
    logging.info(json.dumps(event))
    body = event["body"]
    
    body_split = body.split("&")
    print(body_split)
    #evt_slack = body["event"]
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
    print(evt_slack["text"])
    txt_message = urllib.parse.unquote(evt_slack["text"])
    print(txt_message)
    message = txt_message
    print(txt_message)
    if re.match("set.<https:\/\/charasheet\.vampire-blood\.net\/.*" , txt_message):
        logging.info("setting start")

        match_url  = re.match(".*(https?://[\w/:%#\$&\?\(\)~\.=\+\-]+)", txt_message)
        return_message = set_user_params(user_id, match_url.group(1))
    elif "get" == message:
        #match_url  = re.match(".*(https?://[\w/:%#\$&\?\(\)~\.=\+\-]+)", txt_message)
        return_message = get_user_params(user_id)
    elif message in lst_trigger_param:
        param = json.loads(get_user_params(user_id, ""))
        return_message = "【{}】現在値{}".format(message, param[message])
    elif message in lst_trigger_role:
        param = json.loads(get_user_params(user_id, ""))
        lst = param[message]
        num = int(random.randint(1,100))
        num_targ = lst[-1]
        str_result = ""
        if 0 <= int(num_targ) - num :
            str_result = "成功"
        else:
            str_result = "失敗"

        return_message = "{} 【{}】 {}/{} ({}+{})".format(str_result, message, num, lst[-1], lst[-1], 0)
    elif message in lst_trigger_action:
        param = json.loads(get_user_params(user_id, ""))
        lst = param[message]
        num = int(random.randint(1,100))
        num_targ = lst[-1]
        str_result = ""
        if 0 <= int(num_targ) - num :
            str_result = "成功"
        else:
            str_result = "失敗"

        return_message = "{} 【{}】 {}/{} ({}+{})".format(str_result, message, num, lst[-1], lst[-1], 0)
    elif "景気づけ" == message:
        num = int(random.randint(1,100))
        return_message = "景気づけ：{}".format(num)
    elif "素振り" == message:
        num = int(random.randint(1,100))
        return_message = "素振り：{}".format(num)
    elif "起床ガチャ" == message:
        num = int(random.randint(1,100))
        return_message = "起床ガチャ：{}".format(num)

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
        
    elif "ステータス" == message:
        param = json.loads(get_user_params(user_id, ""))
        return_message = "【{}】\nHP {}/{}　　MP {}/{}　　SAN{}/{}".format(param["name"], param["HP"],param["HP"],param["MP"],param["MP"],param["現在SAN"],param["初期SAN"])

    else:
        return build_response("@{} norm message".format(user_id))

    return {
        "isBase64Encoded": False,
        "statusCode": 200,
        "headers": {},
        "body": json.dumps({
            "icon_emoji": "books",
            "response_type": "in_channel",
            "text": return_message
        })
    }
