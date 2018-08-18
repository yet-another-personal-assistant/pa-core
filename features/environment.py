from runner import Runner

def before_all(context):
    context.runner = Runner()
    context.runner.update_config({"main": {"command": "./main.py", "type": "stdio"}})
