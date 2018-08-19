from runner import Runner

def before_all(context):
    context.runner = Runner()
    context.runner.add("main", "./main.py")
