import requests
import json
import boto3

import yig.config


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


def get_state_data(user_id):
    """
    get_state_data function is get state file.
    """

    key_state = user_id + yig.config.STATE_FILE_PATH

    s3obj = boto3.resource('s3')
    bucket = s3obj.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    obj = bucket.Object(key_state)
    response = obj.get()
    body = response['Body'].read()
    return json.loads(body.decode('utf-8'))


def set_state_data(user_id, state_data):
    """
    set_state function is update PC state param.
    """
    key_state = user_id + yig.config.STATE_FILE_PATH
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    obj_state = bucket.Object(key_state)
    body_state = json.dumps(state_data, ensure_ascii=False)
    obj_state.put(
        Body=body_state.encode('utf-8'),
        ContentEncoding='utf-8',
        ContentType='text/plane'
    )


def get_user_param(user_id, pc_id=None):
    """
    get_user_params function is PC parameter from AWS S3
    """
    key = ""
    if pc_id is None:
        dict_state = get_state_data(user_id)
        key = user_id + "/" + dict_state["pc_id"] + ".json"
    else:
        key = user_id + "/" + pc_id + ".json"
    s3obj = boto3.resource('s3')
    bucket = s3obj.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    obj = bucket.Object(key)
    response = obj.get()
    body = response['Body'].read()
    return json.loads(body.decode('utf-8'))

