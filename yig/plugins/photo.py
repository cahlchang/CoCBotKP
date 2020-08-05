import requests
import os
import boto3

from yig.bot import listener
from yig.util import get_state_data, get_charaimage
import yig.config


@listener("SAVEIMG")
def save_image(bot):
    """This function saves the slack icon image to S3.
    """
    state_data = get_state_data(bot.user_id)
    icon_url = bot.data_user["profile"]["image_512"]
    response = requests.get(icon_url, stream=True)
    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        exception = Exception("Content-Type: " + content_type)
        raise exception

    filename = "%s%s" % (state_data["pc_id"], "_image")

    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    key_image = "%s/%s" % (bot.user_id, filename)
    # todo 上書きを禁止する
    bucket.upload_fileobj(response.raw, key_image)

    return "アイコンを保存しました。", yig.config.COLOR_ATTENTION


@listener("LOADIMG")
def load_image(bot):
    """This function upload icon from s3
    """
    state_data = get_state_data(bot.user_id)
    image = get_charaimage(bot.user_id, state_data["pc_id"])
    param = {
        'token': bot.token,
        "channels": bot.channel_id
    }
    res = requests.post(url="https://slack.com/api/files.upload",
                        params=param,
                        files={'files': image})

    return "アイコン画像をロードしました。", yig.config.COLOR_ATTENTION
