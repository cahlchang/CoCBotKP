from importlib import import_module
from glob import glob
from yig.util import post_command
from yig.util import post_result

import re

KEY_MATCH_FLAG = 0
RE_MATCH_FLAG = 1

command_manager = {
    KEY_MATCH_FLAG: [],
    RE_MATCH_FLAG: []
}

class Bot(object):
    global command_list

    def __init__(self,
                 user_id,
                 token,
                 message,
                 key,
                 data_user,
                 channel_id,
                 response_url):
        self.user_id = user_id
        self.token = token
        self.message = message
        self.key = key
        self.data_user = data_user
        self.channel_id = channel_id
        self.response_url = response_url

        self.init_plugins()

    def init_plugins(self):
        module_list = glob('yig/plugins/*.py')
        for module in module_list:
            module = module.split(".")[0]
            print(".".join(module.split("/")))
            import_module(".".join(module.split("/")))

    def dispatch(self):
        for command_datum in command_manager[KEY_MATCH_FLAG]:
            if self.key == command_datum["command"]:
                post_command(self.message,
                             self.token,
                             self.data_user,
                             self.channel_id)
                return_message, color = command_datum["function"](self)
                post_result(self.response_url,
                            self.user_id,
                            return_message,
                            color)
                return True

        for command_datum in command_manager[RE_MATCH_FLAG]:
            if re.match(command_datum["command"], self.message):
                post_command(self.message,
                             self.token,
                             self.data_user,
                             self.channel_id)
                return_message, color = command_datum["function"](self)
                post_result(self.response_url,
                            self.user_id,
                            return_message,
                            color)
                return True
        return False

    def test(self):
        print("test")
        for command_datum in command_manager[KEY_MATCH_FLAG]:
            print(command_datum["command"])
            print(command_datum["function"])
            command_datum["function"](self)


def listener(command_string, flag=KEY_MATCH_FLAG):
    def wrapper(self):
        global command_manager
        command_manager[flag].append({"command": command_string,
                                      "function": self})

    return wrapper
