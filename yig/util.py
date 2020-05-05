import requests
import json

def post_command(message, token, data_user, channel_id, is_replace_plus=False):
    command_url = "https://slack.com/api/chat.postMessage?"
    if is_replace_plus:
        message = message.replace("+", " ")

    payload = {
        "token": token,
        # "as_user": True,
        "username": data_user["profile"]["display_name"],
        "icon_url": data_user["profile"]["image_1024"],
        "channel": channel_id,
        "text": f"/cc {message}"
    }
    print(payload)
    res = requests.get(command_url, params=payload)
    print(res.url)


def post_result(response_url, user_id, return_message, color, response_type="in_channel"):
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
