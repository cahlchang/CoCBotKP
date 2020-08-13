import requests
import json
import boto3
import imghdr
import os
import copy
from PIL import Image

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


def get_pc_icon_url(team_id, user_id, pc_id):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    file_name = f"{team_id}/{user_id}/{pc_id}.png"
    obj = list(bucket.objects.filter(Prefix=file_name))
    if len(obj) > 0:
        return f"https://wheellab-coc-pcparams.s3.ap-northeast-1.amazonaws.com/{team_id}/{user_id}/{pc_id}.png"
    else:
        return "https://wheellab-coc-pcparams.s3.ap-northeast-1.amazonaws.com/public/noimage.png"


def post_command(message,
                 token,
                 response_url,
                 data_user,
                 channel_id,
                 is_replace_plus=False):
    command_url = "https://slack.com/api/chat.postMessage?" if response_url is not None else response_url
    if is_replace_plus:
        message = message.replace("+", " ")

    payload = {
        "token": token,
        "username": data_user["profile"]["display_name"],
        "icon_url": data_user["profile"]["image_1024"],
        "channel": channel_id,
        "as_user": False,
        "text": f"/cc {message}"
    }
    res = requests.get(command_url, params=payload)
    print(res.text)
    print(res.url)


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
        print(res.url)

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


def write_pc_image(team_id, user_id, pc_id, url):
    """Convert the image to a png image and write it in S3."""
    image_origin_path = f"/tmp/origin_image"
    image_converted_path = f"/tmp/{pc_id}.png"
    image_key = f"{team_id}/{user_id}/{pc_id}.png"

    response = requests.get(url, stream=True)
    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        exception = Exception("Content-Type: " + content_type)
        raise exception

    with open(image_origin_path, 'wb') as f:
        f.write(response.content)

    image = Image.open(image_origin_path)
    image.save(image_converted_path)

    s3_client = boto3.client('s3')
    s3_client.upload_file(image_converted_path, yig.config.AWS_S3_BUCKET_NAME, image_key)

    response = s3_client.put_object_tagging(
        Bucket = yig.config.AWS_S3_BUCKET_NAME,
        Key = image_key,
        Tagging = {'TagSet': [ { 'Key': 'public-object', 'Value': 'yes' }, ]})
    return image_key


def get_charaimage(team_id, user_id, pc_id):
    """get chara image from pc_id"""
    s3_client = boto3.client('s3')

    filename = f"{pc_id}.png"
    key_image = "%s/%s/%s" % (team_id, user_id, filename)
    print(key_image)
    with open(f'/tmp/{filename}', 'wb') as fp:
        s3_client.download_fileobj(yig.config.AWS_S3_BUCKET_NAME, key_image, fp)

    image = None
    with open(f'/tmp/{filename}', 'rb') as f:
        image = f.read()

    return image


def get_now_status(status_name, user_param, state_data, status_name_alias=None):
    current_status = user_param[status_name] if status_name_alias is None else user_param[status_name_alias]

    if status_name in state_data:
        current_status = int(current_status) + int(state_data[status_name])
    return current_status


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
