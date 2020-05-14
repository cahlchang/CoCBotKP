import boto3
import json

from yig.bot import listener

import yig.config

@listener("LIST CHARA")
def show_list_chara(bot):
    """
    show my chara from s3
    """
    lst_chara = get_all_chara_data(bot.user_id)
    lst_show = []
    for chara_data in lst_chara:
        if "name" not in chara_data:
            continue
        name = chara_data["name"].replace('\u3000', '')
        lst_show.append("%s - %s" % (chara_data["pc_id"], name))
    return "%s" % ("\n").join(lst_show), yig.config.COLOR_ATTENTION

    
def get_all_chara_data(user_id):
    key_prefix = "%s/" % user_id
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(yig.config.AWS_S3_BUCKET_NAME)
    lst_object = bucket.objects.filter(Prefix=key_prefix).limit(count=1000)

    lst_chara = []
    for obj in lst_object:
        response = obj.get()
        try:
            lst_chara.append(json.loads(response['Body'].read().decode('utf-8')))
        except Exception as e:
            print(e)

    return lst_chara
