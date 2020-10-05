from importlib import import_module
from glob import glob
from yig.util.data import post_command, post_result, format_as_command, write_user_data, read_user_data
import urllib.parse

import yig.config

import logging

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
    user_id = response_url = key = message = token = data_user = channel_id = channel_name = team_id = trigger_id = api_app_id = view_id = ""

    def __init__(self):
        self.init_plugins()

    def init_param(self, evt_slack):
        print(evt_slack)
        self.user_id = evt_slack["user_id"]
        self.response_url = urllib.parse.unquote(evt_slack["response_url"])
        self.message = urllib.parse.unquote_plus(evt_slack["text"])

        # bad hack
        if self.message.split(' ') and self.message.split(' ')[-1].isnumeric():
            self.message = ' '.join(self.message.split(' ')[:-1]) + "+" + self.message.split(' ')[-1]

        self.channel_id = urllib.parse.unquote(evt_slack["channel_id"])
        self.channel_name = urllib.parse.unquote(evt_slack["channel_name"])
        self.team_id = urllib.parse.unquote(evt_slack["team_id"])
        self.key = format_as_command(self.message)

        payload = {"token": self.get_token(self.team_id),
                   "user": self.user_id}
        res = requests.get("https://slack.com/api/users.profile.get",
                           params=payload,
                           headers={'Content-Type': 'application/json'})
        self.data_user = json.loads(res.text)


    def init_modal(self, body):
        contents = body.split("=")
        param_json = json.loads(urllib.parse.unquote(contents[-1]))
        self.team_id = param_json["user"]["team_id"]
        self.user_id = param_json["user"]["id"]
        self.trigger_id = param_json["trigger_id"]
        payload = {"token": self.get_token(self.team_id),
                   "user": self.user_id}
        view_function = list(filter(lambda x: x["command"] == "VIEW_MODAL", command_manager[KEY_MATCH_FLAG]))[0]["function"]
        view_function(self)


    def confirm_modal(self, body):
        contents = body.split("=")
        param_json = json.loads(urllib.parse.unquote(contents[-1]))
        self.team_id = param_json["user"]["team_id"]
        self.user_id = param_json["user"]["id"]
        self.trigger_id = param_json["trigger_id"]
        self.api_app_id = param_json["api_app_id"]
        # payload = {"token": self.get_token(self.team_id),
        #            "user": self.user_id}
        # res = requests.get("https://slack.com/api/users.profile.get",
        #                    params=payload,
        #                    headers={'Content-Type': 'application/json'})
        # self.data_user = json.loads(res.text)
        if "static_select" in body:
            self.key = self.message = param_json["actions"][0]["selected_option"]["value"]
            modal = "VIEW_CONFIRM_SELECT_MODAL"

        view_function = list(filter(lambda x: x["command"] == modal, command_manager[KEY_MATCH_FLAG]))[0]["function"]
        view_function(self)


    def modal_dispatch(self, body):
        contents = body.split("=")
        param_json = json.loads(urllib.parse.unquote(contents[-1]))
        self.team_id = param_json["user"]["team_id"]
        self.user_id = param_json["user"]["id"]
        self.trigger_id = param_json["trigger_id"]
        map_id = json.loads(read_user_data(self.team_id, self.user_id, "key_id"))
        if "channel_id" in map_id:
            self.channel_id = map_id["channel_id"]
            self.view_id = map_id["view_id"]

        # チャンネルのselecterが叩かれた場合
        if "actions" in param_json and param_json["actions"][0]["action_id"] == "modal-dispatch-no-trans-channel":
            for data in param_json["actions"]:
                if data["type"] == "conversations_select":
                    channel_id = data["selected_conversation"]
                    map_id["channel_id"] = channel_id
                    write_user_data(self.team_id, self.user_id, "key_id", json.dumps(map_id))
            return
        payload = {"token": self.get_token(self.team_id),
                   "user": self.user_id}
        res = requests.get("https://slack.com/api/users.profile.get",
                           params=payload,
                           headers={'Content-Type': 'application/json'})
        self.data_user = json.loads(res.text)
        if "modal-dispatch_in_select" in body:
            for k, datum in param_json["view"]["state"]["values"].items():
                for kk, each in datum.items():
                    self.key = self.message = each["value"]
                    self.dispatch()

        if "modal-dispatch_go_button" in body:
             self.key = self.message = param_json["actions"][0]["value"].upper()
             self.dispatch()
             modal = "VIEW_CONFIRM_EXECUTED_MODAL"

             view_function = list(filter(lambda x: x["command"] == modal, command_manager[KEY_MATCH_FLAG]))[0]["function"]
             view_function(self)


    def init_plugins(self):
        module_list = glob('yig/plugins/*.py')
        for module in module_list:
            module = module.split(".")[0]
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
                         self.channel_id,
                         self.team_id,
                         self.user_id)
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
        print(key_ws)
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
