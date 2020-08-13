from importlib import import_module
from glob import glob
from yig.util import post_command
from yig.util import post_result

import yig.config

import re
import json
import boto3
import requests
import os

RE_NOPOST_COMMANG_FLAG = 0
KEY_MATCH_FLAG = 1
KEY_IN_FLAG = 2
RE_MATCH_FLAG = 3
LAST_EVALUATION_FLAG = 4

command_manager = {
    RE_NOPOST_COMMANG_FLAG: [],
    KEY_MATCH_FLAG: [],
    KEY_IN_FLAG: [],
    RE_MATCH_FLAG: [],
    LAST_EVALUATION_FLAG: []
}

class Bot(object):
    global command_list
    user_id = ""
    response_url = ""
    key = ""
    message = ""
    token = ""
    data_user = None
    channel_id = ""
    team_id = ""

    def __init__(self):
        self.init_plugins()

    def init_param(self,
                   user_id,
                   response_url,
                   key,
                   message,
                   channel_id,
                   team_id):
        self.user_id = user_id
        self.response_url = response_url
        self.key = key
        self.message = message
        self.channel_id = channel_id
        self.team_id = team_id

        payload = {"token": self.get_token(self.team_id),
                   "user": self.user_id}
        res = requests.get("https://slack.com/api/users.profile.get",
                           params=payload,
                           headers={'Content-Type': 'application/json'})
        self.data_user = json.loads(res.text)

    def init_plugins(self):
        module_list = glob('yig/plugins/*.py')
        for module in module_list:
            module = module.split(".")[0]
            print(".".join(module.split("/")))
            import_module(".".join(module.split("/")))

    def install_bot(self, event):
        if event["params"]["path"] == {}:
            print("redirect test")
            param = {
                "client_id": os.environ["CLIENT_ID"],
                "client_secret": os.environ["CLIENT_SECRET"],
                "code": event["params"]["querystring"]["code"],
                "redirect_url": os.environ["REDIRECT_URL"]
            }
            res = requests.post("https://slack.com/api/oauth.v2.access", params=param)
            data_init = json.loads(res.text)
            token = data_init["access_token"]
            team_id = data_init["team"]["id"]
            team_name = data_init["team"]["name"]
            key_ws = "%s/workspace.json" % team_id
            s3_client = boto3.resource('s3')
            bucket = s3_client.Bucket(yig.config.AWS_S3_BUCKET_NAME)
            data_ws = {'name': team_name,
                       'id': team_id,
                       'token': token}
            obj = bucket.Object(key_ws)
            body = json.dumps(data_ws, ensure_ascii=False)
            response = obj.put(
                Body=body.encode('utf-8'),
                ContentEncoding='utf-8',
                ContentType='text/plane'
            )
            return "ok"

    def dispatch(self):
        def process():
            post_command(self.message,
                         self.token,
                         self.data_user,
                         self.channel_id)
            return_content, color = command_datum["function"](self)
            post_result(self.token,
                        self.user_id,
                        self.channel_id,
                        return_content,
                        color)

        # 辛くなったら直す
        for command_datum in command_manager[RE_NOPOST_COMMANG_FLAG]:
            if re.match(command_datum["command"], self.message, flags=re.IGNORECASE):
                return_content, color = command_datum["function"](self)
                post_result(self.token,
                            self.user_id,
                            self.channel_id,
                            return_content,
                            color)
                return True

        for command_datum in command_manager[KEY_MATCH_FLAG]:
            if self.key == command_datum["command"]:
                process()
                return True

        for command_datum in command_manager[KEY_IN_FLAG]:
            if self.key in command_datum["command"]:
                process()
                return True

        for command_datum in command_manager[RE_MATCH_FLAG]:
            if re.match(command_datum["command"], self.message, flags=re.IGNORECASE):
                process()
                return True

        for command_datum in command_manager[LAST_EVALUATION_FLAG]:
            process()
            return True

        return False

    def get_token(self, team_id):
        s3_resource = boto3.resource('s3')
        bucket = s3_resource.Bucket(yig.config.AWS_S3_BUCKET_NAME)
        key_ws = "%s/workspace.json" % team_id
        obj = bucket.Object(key_ws)
        response = obj.get()
        body = response['Body'].read()
        self.token = json.loads(body.decode('utf-8'))['token']
        return self.token

    def get_listener(self):
        return command_manager


def listener(command_string, flag=KEY_MATCH_FLAG):
    def wrapper(self):
        global command_manager
        command_manager[flag].append(
            {
                "command": command_string,
                "function": self
            })
    return wrapper
