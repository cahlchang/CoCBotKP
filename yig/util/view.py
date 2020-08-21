import requests
import json
import boto3
import os
import copy
from PIL import Image

import yig.config


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


def get_pc_icon_url(team_id, user_id, pc_id):
    s3_client = boto3.resource('s3')
    bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    file_name = f"{team_id}/{user_id}/{pc_id}.png"
    obj = list(bucket.objects.filter(Prefix=file_name))
    if len(obj) > 0:
        return f"https://wheellab-coc-pcparams.s3.ap-northeast-1.amazonaws.com/{team_id}/{user_id}/{pc_id}.png"
    else:
        return "https://wheellab-coc-pcparams.s3.ap-northeast-1.amazonaws.com/public/noimage.png"


def section_builder(lst_document):
    section_content = []
    for document in lst_document:
        section_content.append({"type": "mrkdwn",
                                "text": document})
    section = {"type": "section",
               "fields": section_content}
    return section


def divider_builder():
    return {"type": "divider"}
