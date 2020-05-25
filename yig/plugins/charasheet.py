import requests
import boto3
import re
import json

from yig.bot import listener, RE_MATCH_FLAG
from yig.util import get_state_data

import yig.config

@listener(r"init.<https://charasheet.vampire-blood.net/.*", RE_MATCH_FLAG)
def init_charasheet_with_vampire(bot):
    """
    This function init charasheet
    """
    matcher = re.match(r".*<(https.*)>", bot.message)

    url = matcher.group(1) + ".json"
    res = requests.get(url)
    request_json = json.loads(res.text)
    param_json = format_param_json(bot, request_json)

    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    key = "%s/%s.json" % (param_json["user_id"], param_json["pc_id"])
    obj = bucket.Object(key)
    body = json.dumps(param_json, ensure_ascii=False)
    response = obj.put(
        Body=body.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )

    #todo 力尽きたのであとでいい感じにする
    STATE_FILE_PATH = "/state.json"
    key_state = param_json["user_id"] + STATE_FILE_PATH
    dict_state = {
        "url": url,
        "pc_id": "%s" % param_json["pc_id"]
    }
    obj_state = bucket.Object(key_state)
    body_state = json.dumps(dict_state, ensure_ascii=False)
    response = obj_state.put(
        Body=body_state.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )

    return get_status_message("INIT CHARA", param_json, dict_state), yig.config.COLOR_ATTENTION


@listener(r"^(u|update)$", RE_MATCH_FLAG)
def update_charasheet_with_vampire(bot):
    color = yig.config.COLOR_ATTENTION
    state_data = get_state_data(bot.user_id)
    url = state_data["url"]
    res = requests.get(url)
    request_json = json.loads(res.text)
    param_json = format_param_json(bot, request_json)

    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    key = "%s/%s.json" % (param_json["user_id"], param_json["pc_id"])
    obj = bucket.Object(key)
    body = json.dumps(param_json, ensure_ascii=False)
    response = obj.put(
        Body=body.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )

    return get_status_message("UPDATE", param_json, state_data), color


# todo いい感じにする
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


# todo 技能の定義なんとかならないか。。。
def format_param_json(bot, request_json):
    param_json = {}

    REPLACE_PARAMETER = {
        "NP1": "STR",
        "NP2": "CON",
        "NP3": "POW",
        "NP4": "DEX",
        "NP5": "APP",
        "NP6": "SIZ",
        "NP7": "INT",
        "NP8": "EDU",
        "NP9": "HP",
        "NP10": "MP",
        "NP11": "初期SAN",
        "NP12": "アイデア",
        "NP13": "幸運",
        "NP14": "知識"}
    
    tba_replace = ["回避",
                   "キック",
                   "組み付き",
                   "こぶし（パンチ）",
                   "頭突き",
                   "投擲",
                   "マーシャルアーツ",
                   "拳銃",
                   "サブマシンガン",
                   "ショットガン",
                   "マシンガン",
                   "ライフル"]

    tfa_replace = ["応急手当",
                   "鍵開け",
                   "隠す",
                   "隠れる",
                   "聞き耳",
                   "忍び歩き",
                   "写真術",
                   "精神分析",
                   "追跡",
                   "登攀",
                   "図書館",
                   "目星"]

    taa_replace = ["運転",
                   "機械修理",
                   "重機械操作",
                   "乗馬",
                   "水泳",
                   "製作",
                   "操縦",
                   "跳躍",
                   "電気修理",
                   "ナビゲート",
                   "変装"]

    tca_replace = ["言いくるめ",
                   "信用",
                   "説得",
                   "値切り",
                   "母国語"]
    tka_replace = ["医学",
                   "オカルト",
                   "化学",
                   "クトゥルフ神話",
                   "芸術",
                   "経理",
                   "考古学",
                   "コンピューター",
                   "心理学",
                   "人類学",
                   "生物学",
                   "地質学",
                   "電子工学",
                   "天文学",
                   "博物学",
                   "物理学",
                   "法律",
                   "薬学",
                   "歴史"]

    for key, param in REPLACE_PARAMETER.items():
          param_json[param] = request_json[key]
    
    def replace_role_param(key, lst_key_roles):
        return_data = {}
        if f"{key}Name" in request_json:
            for custom_added_name in request_json[f"{key}Name"]:
                lst_key_roles.append(custom_added_name)
            
        for idx, param in enumerate(lst_key_roles):
            lst = []
            lst.append(request_json[f"{key}D"][idx])
            lst.append(request_json[f"{key}S"][idx])
            lst.append(request_json[f"{key}K"][idx])
            lst.append(request_json[f"{key}A"][idx])
            lst.append(request_json[f"{key}O"][idx])
            lst.append(request_json[f"{key}P"][idx])
            return_data[param] = [i if i != "" else 0 for i in lst]
        return return_data
    
    param_json.update(replace_role_param("TBA", tba_replace))
    param_json.update(replace_role_param("TFA", tfa_replace))
    param_json.update(replace_role_param("TAA", taa_replace))
    param_json.update(replace_role_param("TCA", tca_replace))
    param_json.update(replace_role_param("TKA", tka_replace))
    
    def add_spec_param(spec_param, name):
        param = request_json[spec_param]
        return {f"{name}（{param}）": param_json[name]}

    param_json.update(add_spec_param("unten_bunya", "運転"))
    param_json.update(add_spec_param("seisaku_bunya", "製作"))
    param_json.update(add_spec_param("main_souju_norimono", "操縦"))
    param_json.update(add_spec_param("mylang_name", "母国語"))
    param_json.update(add_spec_param("geijutu_bunya", "芸術"))

    param_json["現在SAN"] = request_json["SAN_Left"]
    param_json["最大SAN"] = request_json["SAN_Max"]

    param_json["user_id"] = bot.user_id
    param_json["name"] = request_json["pc_name"]
    param_json["pc_id"] = request_json["data_id"]
    param_json["DB"] = request_json["dmg_bonus"]
    param_json["memo"] = request_json["pc_making_memo"]

    return param_json
