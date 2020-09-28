import requests
import json
import boto3
import imghdr
import os
import copy
from botocore.exceptions import ClientError
from PIL import Image

import yig.config


def write_user_data(team_id, user_id, filename, content):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    user_dir = f"{team_id}/{user_id}"
    obj = bucket.Object(f"{user_dir}/{filename}")
    response = obj.put(
        Body=content,
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )


def write_session_data(team_id, path, content):
    try:
        s3_client = boto3.resource('s3')
        bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
        obj = bucket.Object(f"{team_id}/{path}")
        response = obj.put(
            Body=content,
            ContentEncoding='utf-8',
            ContentType='text/plane'
        )
    except ClientError as e:
        print(e)


def read_user_data(team_id, user_id, filename):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    user_dir = f"{team_id}/{user_id}"
    obj = bucket.Object(f"{user_dir}/{filename}")
    response = obj.get()
    return response['Body'].read()


def read_session_data(team_id, path):
    try:
        s3_client = boto3.resource('s3')
        bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
        obj = bucket.Object(f"{team_id}/{path}")
        response = obj.get()
        return response['Body'].read()
    except ClientError as e:
        print(e)
        return None


def post_command(message,
                 token,
                 data_user,
                 channel_id,
                 team_id,
                 user_id,
                 is_replace_plus=False):
    command_url = "https://slack.com/api/chat.postMessage?"
    if is_replace_plus:
        message = message.replace("+", " ")

    payload = {
        "token": token,
        "username": data_user["profile"]["display_name"],
        "icon_url": data_user["profile"]["image_72"],
        "channel": channel_id,
        "text": f"/cc {message}"
    }
    res = requests.get(command_url, params=payload)
    print(res.text)


def post_result(token,
                user_id,
                channel_id,
                return_content,
                color):
    command_url = "https://slack.com/api/chat.postMessage?"
    payload = {
        "token": token,
        "channel": channel_id
    }
    def request(command_url, payload):
        print(payload)
        res = requests.post(command_url, params=payload)
        print(res.text)

    if isinstance(return_content, str):
        normal_format = {
            "text": "<@{}>".format(user_id),
            "attachments": json.dumps([
                {
                    "text": return_content,
                    "type": "mrkdwn",
                    "color": color
                }])
        }
        payload.update(normal_format)
        request(command_url, payload)
    elif isinstance(return_content, list):
        for one_payload in return_content:
            use_payload = copy.copy(payload)
            use_payload.update(one_payload)
            request(command_url, use_payload)
    else:
        payload.update(return_content)
        request(command_url, payload)


def get_pc_icon_url(team_id, user_id):
    url = f"https://d13xcuicr0q687.cloudfront.net/{team_id}/{user_id}/icon.png"
    response = requests.head(url)
    if response.status_code == 403:
        return "https://d13xcuicr0q687.cloudfront.net/public/noimage.png"
    else:
        return f"https://d13xcuicr0q687.cloudfront.net/{team_id}/{user_id}/icon.png"


def get_state_data(team_id, user_id):
    """get_state_data function is get state file."""
    return json.loads(read_user_data(team_id, user_id, yig.config.STATE_FILE_PATH).decode('utf-8'))


def set_state_data(team_id, user_id, state_data):
    """set_state function is update PC state param."""
    write_user_data(team_id, user_id, yig.config.STATE_FILE_PATH, json.dumps(state_data, ensure_ascii=False))


def get_user_param(team_id, user_id, pc_id=None):
    """get_user_params function is PC parameter from AWS S3"""
    key_pc_id = pc_id
    if pc_id is None:
        key_pc_id = get_state_data(team_id, user_id)["pc_id"]

    return json.loads(read_user_data(team_id, user_id, f"{key_pc_id}.json").decode('utf-8'))


def get_now_status(status_name, user_param, state_data, status_name_alias=None):
    current_status = user_param[status_name] if status_name_alias is None else user_param[status_name_alias]

    if status_name in state_data:
        current_status = int(current_status) + int(state_data[status_name])
    return current_status


def get_basic_status(user_param, state_data):
    now_hp = get_now_status('HP', user_param, state_data)
    max_hp = user_param['HP']
    now_mp = get_now_status('MP', user_param, state_data)
    max_mp = user_param['MP']
    now_san = get_now_status('SAN', user_param, state_data, '現在SAN')
    max_san = user_param['現在SAN']
    db = user_param['DB']
    return now_hp, max_hp, now_mp, max_mp, now_san, max_san, db

def view_modal(bot):
    command_url = "https://slack.com/api/views.open"
    payload = {
        "token": bot.token,
        "channel": bot.channel_id
    }
    view_content = {
    "type": "modal",
    "callback_id": "modal-identifier",
    "title": {
      "type": "plain_text",
      "text": "Just a modal"
    },
    "blocks": [
      {
        "type": "section",
        "block_id": "section-identifier",
        "text": {
          "type": "mrkdwn",
          "text": "*Welcome* to ~my~ Block Kit _modal_!"
        },
        "accessory": {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "Just a button"
          },
          "action_id": "button-identifier"
        }
      }
    ]

    payload = {
        "token": bot.token,
        "channel": bot.channel_id,
        "trigger_id": bot.trigger_id,
        "view": json.dumps(view_content, ensure_ascii=False)
    }

    print(payload)
    res = requests.post(command_url, params=payload)
    print(res.text)


def format_as_command(text: str) -> str:
    """
    Make text uppercased and remove edge spaces
    """
    return text.upper().strip()


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
