import boto3
import json
import re

from yig.bot import listener, RE_MATCH_FLAG

import yig.config

@listener("list chara.*", RE_MATCH_FLAG)
def show_list_chara(bot):
    """
    show my chara from s3
    """
    matcher_param = re.match("LIST CHARA (.*)", bot.key)
    param_condition = None
    operant_condition = None
    value_condition = None

    if matcher_param:
        condition = matcher_param.group(1)
        matcher_operant = re.match(r"(.*)(\&GT;|\&LT;)(.*)", condition)
        if matcher_operant:
            param_condition = matcher_operant.group(1)
            operant_condition = matcher_operant.group(2)
            value_condition = matcher_operant.group(3)
        else:
            param_condition = condition

    lst_chara = get_all_chara_data(bot.user_id)
    lst_show = []
    lst_cond_data = []
    for chara_data in lst_chara:
        param_chara = 0
        if "name" not in chara_data:
            continue
        name = chara_data["name"].replace('\u3000', '')
        if "url" not in chara_data:
            chara_data["url"] = "https://charasheet.vampire-blood.net/%s" % chara_data["pc_id"]

        str_set = ""
        if param_condition:
            if isinstance(chara_data[param_condition], list):
                param_chara = int(chara_data[param_condition][-1])
            else:
                param_chara = int(chara_data[param_condition])

            if operant_condition:
                value_condition = int(value_condition)
                if operant_condition == "&LT;":
                    if param_chara >= value_condition:
                        continue
                else:
                    if param_chara <= value_condition:
                        continue

            str_set = "<%s|%s - %s %s *%s*>" % (chara_data["url"],
                                                chara_data["pc_id"],
                                                name,
                                                param_condition,
                                                param_chara)
            lst_cond_data.append({"param": param_chara, "text": str_set})
        else:
            str_set = "<%s|%s - %s>" % (chara_data["url"],
                                        chara_data["pc_id"],
                                        name)
            lst_show.append(str_set)

    if param_condition:
        lst_sorted = sorted(lst_cond_data, key=lambda x:x['param'], reverse=True)
        for data in lst_sorted:
            lst_show.append(data["text"])

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
            data_chara = json.loads(response['Body'].read().decode('utf-8'))
            lst_chara.append(data_chara)
        except Exception as e:
            print(e)

    return lst_chara
