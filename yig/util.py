import requests

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
