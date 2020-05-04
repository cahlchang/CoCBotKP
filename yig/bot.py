from importlib import import_module
from glob import glob

command_list = []

class Bot(object):
    global command_list
    key = ""
    
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
                command_datum["function"](self)

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
