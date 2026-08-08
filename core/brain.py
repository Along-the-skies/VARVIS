# Jarvis Brain
# Command processing and decision making
from modules.apps import open_app, close_app
from  core.logger import Logger
from modules.system import system_info
from modules.settings import change_settings
from models.model import understand_command
Logger.info("Brain module loaded")

def process_command(command):
    result = understand_command(command)

    if result["type"] == "chat":
        return result["content"]

    command = result["content"]

    parts = command.lower().split()

    if len(parts) < 2:
        return
    if len(parts) == 2:
        action,app = parts
        print(action, app)
    elif len(parts) == 3:
        action,app,value = parts
        print(action,app,value)

    if action == "open":
        return open_app(app)

    elif action == "close":
        return close_app(app)

    elif action == "check":
        return system_info(app)

    elif action == "change":
        return change_settings(app,value)

    else:
        return f"Unknown command: {action}"