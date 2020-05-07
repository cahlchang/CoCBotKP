import requests
import json
import boto3

import yig

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
    print(payload)
    res = requests.get(command_url, params=payload)
    print(res.url)


def post_result(response_url,
                user_id,
                return_message,
                color,
                response_type="in_channel"):
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
