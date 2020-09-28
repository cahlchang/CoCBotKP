import requests
import json
import boto3
import os
import math
import gzip
from PIL import Image, ImageDraw, ImageFont

import yig.config


def write_pc_image(team_id, user_id, pc_id, url):
    """Convert the image to a png image and write it in S3."""
    image_origin_path = f"/tmp/origin_image"
    image_converted_path = f"/tmp/{pc_id}.png"
    image_org_key = f"{team_id}/{user_id}/{pc_id}.png"

    response = requests.get(url, stream=True)
    content_type = response.headers["content-type"]
    if 'image' not in content_type:
        exception = Exception("Content-Type: " + content_type)
        raise exception

    with open(image_origin_path, 'wb') as f:
        f.write(response.content)

    image_org = Image.open(image_origin_path)
    image_org.resize((400, 400))
    image_org.save(image_converted_path)

    s3_client = boto3.client('s3')
    s3_client.upload_file(image_converted_path, yig.config.AWS_S3_BUCKET_NAME, image_org_key)

    s3_client.put_object_tagging(
        Bucket = yig.config.AWS_S3_BUCKET_NAME,
        Key = image_org_key,
        Tagging = {'TagSet': [ { 'Key': 'public-object', 'Value': 'yes' }, ]})

    return image_org_key


def create_param_image(team_id, user_id, pc_id, user_param):
    # math define
    n = 8
    W = H = 400
    r = 200
    radian = 2 * math.pi / n;
    w = h = 0
    h_o = 5

    # color define
    white = (255, 255, 255)
    black = (0, 0, 0)
    dimgray = (105, 105, 105)
    gray = (127, 135, 143)
    light_sky_blue = (180, 235, 250)

    font = ImageFont.truetype("font/04Takibi-Medium.otf", 48)
    lst_param_name = ["STR", "CON", "POW", "DEX", "APP", "SIZ", "INT", "EDU"]

    canvas = Image.new('RGB', (W, H), white)
    draw = ImageDraw.Draw(canvas)
    lst_coord =[]
    for i in range(0, 9):
        cood = (math.cos(i*radian)*r+W/2,
                math.sin(i*radian)*r+H/2)
        lst_coord.append(cood)

    draw.line(lst_coord,
              fill=black,
              width=3)
    params = [float(user_param['POW'])/18,
              float(user_param['DEX'])/18,
              float(user_param['APP'])/18,
              float(user_param['SIZ'])/18,
              float(user_param['INT'])/18,
              float(user_param['EDU'])/21,
              float(user_param['STR'])/18,
              float(user_param['CON'])/18]

    lst_param_cood = []
    for i in range(0, 8):
        param_cood = (math.cos(i*radian)*r*params[i]+W/2,
                      math.sin(i*radian)*r*params[i]+H/2)
        lst_param_cood.append(param_cood)

    draw.polygon(lst_param_cood,
                 outline=black,
                 fill=light_sky_blue)

    def get_point(w, h, i):
        yield [((W-w)/2, h_o), (W-w-h_o, h_o*7), (W-w, H/2-h/2), (W-w-h_o, H-h_o*7-h),
               ((W-w)/2, H-h-h_o), (h_o, H-h_o*7-h), (0, (H-h)/2), (h_o*1, h_o*7), ((W-w)/2, h_o)][i]

    for i, name in enumerate(lst_param_name):
        w, h = draw.textsize(name, font=font)
        draw.text(next(get_point(w, h, i)),
                  name,
                  dimgray,
                  font=font)

    lst_auxiliary_line = [[(W/2, 0), (W/2, H)],[(0, H/2), (W, H/2)],
                          [(math.cos(1*radian)*r+W/2, math.sin(1*radian)*r+H/2),
                           (math.cos(5*radian)*r+W/2, math.sin(5*radian)*r+H/2)],
                          [(math.cos(3*radian)*r+W/2, math.sin(3*radian)*r+H/2),
                           (math.cos(7*radian)*r+W/2, math.sin(7*radian)*r+H/2)]]

    for auxiliary_line in lst_auxiliary_line:
        draw.line(auxiliary_line,
                  fill=gray,
                  width=1)

    lst_inner_line = []
    for j in [1/3, 2/3]:
        lst_each = []
        for i in range(0,9):
            lst_each.append((math.cos(i*radian)*r*j+W/2,
                             math.sin(i*radian)*r*j+H/2))
        lst_inner_line.append(lst_each)

    for inner_line in lst_inner_line:
        draw.line(inner_line,
                  fill=gray,
                  width=1)

    return canvas

def save_param_image(image, path, team_id, user_id, pc_id):
    image_param_path = f"/tmp/{pc_id}_param.png"
    image_param_key = f"{team_id}/{user_id}/{pc_id}_param.png"
    image.save(image_param_path)

    s3_client = boto3.client('s3')
    s3_client.upload_file(image_param_path, yig.config.AWS_S3_BUCKET_NAME, image_param_key)
    s3_client.put_object_tagging(
        Bucket = yig.config.AWS_S3_BUCKET_NAME,
        Key = image_param_key,
        Tagging = {'TagSet': [ { 'Key': 'public-object', 'Value': 'yes' }, ]})

    return f"https://d13xcuicr0q687.cloudfront.net/{team_id}/{user_id}/{pc_id}_param.png"


def get_charaimage(team_id, user_id, pc_id):
    """get chara image from pc_id"""
    s3_client = boto3.client('s3')

    filename = f"{pc_id}.png"
    key_image = "%s/%s/%s" % (team_id, user_id, filename)
    with open(f'/tmp/{filename}', 'wb') as fp:
        s3_client.download_fileobj(yig.config.AWS_S3_BUCKET_NAME, key_image, fp)

    image = None
    with open(f'/tmp/{filename}', 'rb') as f:
        image = f.read()

    return image


def get_pc_image_url(team_id, user_id, pc_id, ts):
    url = f"https://d13xcuicr0q687.cloudfront.net/{team_id}/{user_id}/{pc_id}.png?{ts}"
    response = requests.head(url)
    if response.status_code == 403:
        return "https://d13xcuicr0q687.cloudfront.net/public/noimage.png"
    else:
        return url


def get_param_image_path(team_id, user_id, pc_id):
    return f"{team_id}/{user_id}/{pc_id}_param.png"


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
