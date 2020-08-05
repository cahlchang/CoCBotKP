import requests
import json
import boto3
import imghdr
import os

import yig.config

def write_user_data(team_id, user_id, filename, content):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    user_dir = f"{team_id}/{user_id}"
    obj = bucket.Object(f"{user_dir}/{filename}")
    print(f"{user_dir}/{filename}")
    response = obj.put(
        Body=content,
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )


def read_user_data(team_id, user_id, filename):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    user_dir = f"{team_id}/{user_id}"
    obj = bucket.Object(f"{user_dir}/{filename}")
    print(f"{user_dir}/{filename}")
    response = obj.get()
    return response['Body'].read()


def post_command(message,
                 token,
                 data_user,
                 channel_id,
                 is_replace_plus=False):
    command_url = "https://slack.com/api/chat.postMessage?"
    if is_replace_plus:
        message = message.replace("+", " ")

    payload = {
        "token": token,
        "username": data_user["profile"]["display_name"],
        "icon_url": data_user["profile"]["image_1024"],
        "channel": channel_id,
        "text": f"/cc {message}"
    }
    res = requests.get(command_url, params=payload)
    print(res.text)


def post_result(token,
                user_id,
                channel_id,
                return_content,
                color,
                response_type="in_channel"):
    command_url = "https://slack.com/api/chat.postMessage?"
    payload = {
        "token": token,
        "icon_emoji": "books",
        "channel": channel_id,
        "response_type": response_type,
        "replace_original": False,
        "headers": {}
    }
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
    else:
        payload.update(return_content)
        print(payload)

    res = requests.get(command_url, params=payload)
    print(res.text)


def get_state_data(team_id, user_id):
    """get_state_data function is get state file."""
    return json.loads(read_user_data(team_id, user_id, yig.config.STATE_FILE_PATH).decode('utf-8'))


def set_state_data(team_id, user_id, state_data):
    """set_state function is update PC state param."""
    write_user_data(team_id, user_id, yig.config.STATE_FILE_PATH, json.dumps(state_data, ensure_ascii=False))


def get_user_param(team_id, user_id, pc_id=None):
    """get_user_params function is PC parameter from AWS S3
    """
    key_pc_id = pc_id
    if pc_id is None:
        key_pc_id = get_state_data(team_id, user_id)["pc_id"]

    return json.loads(read_user_data(team_id, user_id, f"{key_pc_id}.json").decode('utf-8'))


def get_charaimage(user_id, pc_id):
    """get chara image from pc_id"""
    s3_client = boto3.client('s3')

    filename = "%s%s" % (pc_id, "_image")
    key_image = "%s/%s" % (user_id, filename)
    with open('/tmp/load_image', 'wb') as fp:
        s3_client.download_fileobj(yig.config.AWS_S3_BUCKET_NAME, key_image, fp)
    imagetype = imghdr.what('/tmp/load_image')
    os.rename('/tmp/load_image', '/tmp/load_image.%s' % imagetype)

    image = None
    with open('/tmp/load_image.%s' % imagetype, 'rb') as f:
        image = f.read()

    return image


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

#def get_charaimage_url(user_id, pc_id):
