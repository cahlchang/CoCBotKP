import requests
import boto3
import os

from yig.bot import listener
from yig.util import get_state_data

import yig.config

@listener("SAVEIMG")
def save_image(bot):
    """
    This function saves the slack icon image to S3.
    """
    state_data = get_state_data(bot.user_id)
    icon_url = bot.data_user["profile"]["image_512"]
    response = requests.get(icon_url, stream=True)
    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        exception = Exception("Content-Type: " + content_type)
        raise exception

    ext = os.path.splitext(icon_url)[1]
    filename = "%s%s" % (state_data["pc_id"], ext)

    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    key_image = "%s/%s" % (bot.user_id, filename)
    # todo 上書きを禁止する
    bucket.upload_fileobj(response.raw, key_image)

    return "アイコンを保存しました。", yig.config.COLOR_ATTENTION

@listener("LOADIMG")
def load_image(bot):
    """
    This function saves the slack icon image to S3.
    """
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    key_image = "%s/%s" % (bot.user_id, filename)
    obj = bucket.Object(key_image)
    response = obj.get()
    body = response['Body'].read()

    url = "https://slack.com/api/users.setPhoto"
    set_params = {'token': bot.user_token,
                  'image': body}
    r = requests.get(url, params=set_params)
    
    return "アイコンを更新しました。", yig.config.COLOR_ATTENTION
