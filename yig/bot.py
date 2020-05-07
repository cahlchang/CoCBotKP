from importlib import import_module
from glob import glob
from yig.util import post_command
from yig.util import post_result

command_list = []

class Bot(object):
    global command_list
    user_id = ""
    response_url = ""
    key = ""
    message = ""
    token = ""
    user_token = ""
    data_user = None
    channel_id = ""

    def __init__(self):
        self.init_plugins()

    def init_plugins(self):
        module_list = glob('yig/plugins/*.py')
        for module in module_list:
            module = module.split(".")[0]
            print(".".join(module.split("/")))
            import_module(".".join(module.split("/")))

    def dispatch(self):
        for command_datum in command_list:
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
        return False

    def test(self):
        print("test")
        for command_datum in command_list:
            print(command_datum["command"])
            print(command_datum["function"])
            command_datum["function"](self)


def listener(command_string):
    def wrapper(self):
        global command_list
        command_list.append({"command": command_string,
                             "function": self})
        
    return wrapper
