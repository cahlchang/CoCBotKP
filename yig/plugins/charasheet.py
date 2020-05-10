import requests
import boto3

from yig.bot import listener, RE_MATCH_FLAG
from yig.util import get_state_data

import yig.config

@listener(r"init.<https://yahoo*>", RE_MATCH_FLAG)
def save_image(bot):
    """
    This function saves the slack icon image to S3.
    """
    # state_data = get_state_data(bot.user_id)
    # icon_url = bot.data_user["profile"]["image_512"]
    # response = requests.get(icon_url, stream=True)
    # content_type = response.headers["content-type"]
    # if 'image' not in content_type:
    #     exception = Exception("Content-Type: " + content_type)
    #     raise exception

    # filename = "%s%s" % (state_data["pc_id"], "_image")

    # s3_client = boto3.resource('s3')
    # bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    # key_image = "%s/%s" % (bot.user_id, filename)
    # # todo 上書きを禁止する
    # bucket.upload_fileobj(response.raw, key_image)

    return "test", yig.config.COLOR_ATTENTION

