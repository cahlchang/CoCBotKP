import boto3
import json
import re
import requests
from yig.bot import listener, RE_MATCH_FLAG

import yig.config

@listener(r"history.<(https.*)>", RE_MATCH_FLAG)
def show_history(bot):
    """:bookmark_tabs: *history chara session*
`/cc history YOUR_CHARACTER_SHEET_URL`
    """
    matcher = re.match(r".*<(https.*)>", bot.message)
    url_plane = matcher.group(1)
    lst_key = search_all_session(bot.team_id, url_plane)

    return "見た目を無視した版です。\n\n" + "\n".join(lst_key), None


def search_all_session(team_id, url_plane):
    url = f"{url_plane}.json"
    response = requests.get(url)
    request_json = json.loads(response.text)
    pc_id = request_json["data_id"]

    # 西暦3000年代かセッション件数1000件超えたら誰か頑張る
    key_prefix = f"{team_id}/2"
    s3_resource = boto3.resource('s3')
    bucket = s3_resource.Bucket(yig.config.AWS_S3_BUCKET_NAME)

    lst_object = bucket.objects.filter(Prefix=key_prefix).limit(count=1000)
    lst_key = []
    for obj in lst_object:
        if str(pc_id) in obj.key:
            lst_key.append(obj.key)
    return lst_key
