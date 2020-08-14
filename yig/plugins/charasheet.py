import requests
import re
import json

from yig.bot import listener, RE_MATCH_FLAG, KEY_IN_FLAG
from yig.util import get_state_data, write_user_data, get_status_message, section_builder, divider_builder, get_basic_status, get_pc_icon_url, get_user_param

import yig.config


@listener(r"init.<https://charasheet.vampire-blood.net/.*", RE_MATCH_FLAG)
def init_charasheet_with_vampire(bot):
    """:pencil: *init charasheet*
`/cc init YOUR_CHARACTER_SHEET_URL`
    """
    matcher = re.match(r".*<(https.*)>", bot.message)
    url_plane = matcher.group(1)
    url = f"{url_plane}.json"
    response = requests.get(url)

    request_json = json.loads(response.text)
    user_param = format_param_json(bot, request_json)
    user_param["url"] = url_plane

    pc_id = user_param["pc_id"]
    key = f"{pc_id}.json"

    write_pc_json = json.dumps(user_param, ensure_ascii=False).encode('utf-8')
    write_user_data(bot.team_id, bot.user_id, key, write_pc_json)

    dict_state = {
        "url": url,
        "pc_id": "%s" % user_param["pc_id"]
    }

    write_state_json = json.dumps(dict_state, ensure_ascii=False).encode('utf-8')
    write_user_data(bot.team_id, bot.user_id, yig.config.STATE_FILE_PATH, write_state_json)

    now_hp, max_hp, now_mp, max_mp, now_san, max_san, db = get_basic_status(user_param, dict_state)
    pc_name = user_param["name"]
    dex = user_param["DEX"]
    block_content = []
    block_content.append(divider_builder())
    image_url = get_pc_icon_url(bot.team_id, bot.user_id, pc_id)
    user_content = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*INIT CHARACTER*\n\n*Name:* <{image_url}|{pc_name}>\n*HP:* {now_hp}/{max_hp} *MP:* {now_mp}/{max_mp} *SAN:* {now_san}/{max_san}\n*DEX:* {dex} *DB:* {db}"
        },
        "accessory": {
            "type": "image",
            "image_url": image_url,
            "alt_text": "image"
        }
    }
    block_content.append(user_content)
    block_content.append(divider_builder())

    payload = [{'blocks': json.dumps(block_content, ensure_ascii=False)}]
    return payload, None


@listener(('U', 'UPDATE'), KEY_IN_FLAG)
def update_charasheet_with_vampire(bot):
    """:arrows_counterclockwise: *update charasheet*
`/cc u`
`/cc update`
    """
    state_data = get_state_data(bot.team_id, bot.user_id)
    user_param_old = get_user_param(bot.team_id, bot.user_id, state_data["pc_id"])

    url = state_data["url"]
    res = requests.get(url)
    request_json = json.loads(res.text)
    param_json = format_param_json(bot, request_json)
    param_json["url"] = user_param_old["url"]
    pc_id = param_json["pc_id"]
    key = f"{pc_id}.json"

    write_pc_json = json.dumps(param_json, ensure_ascii=False).encode('utf-8')
    write_user_data(bot.team_id, bot.user_id, key, write_pc_json)

    return get_status_message("UPDATE", param_json, state_data), yig.config.COLOR_ATTENTION


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
    param_json["job"] = request_json["shuzoku"]
    param_json["age"] = request_json["age"]
    param_json["arms_name"] = request_json["arms_name"]
    param_json["arms_hit"] = request_json["arms_hit"]
    param_json["arms_damage"] = request_json["arms_damage"]
    param_json["arms_attack_count"] = request_json["arms_attack_count"]
    param_json["item_name"] = request_json["item_name"]
    param_json["item_tanka"] = request_json["item_tanka"]
    param_json["item_num"] = request_json["item_num"]
    param_json["item_price"] = request_json["item_price"]
    param_json["item_memo"] = request_json["item_memo"]
    param_json["money"] = request_json["money"]

    return param_json
