import select

from runner import Runner

def before_all(context):
    context.runner = Runner()
    context.runner.add("main", "./main.py", buffering="line")
    context.runner.add("server",
                       command="./server.py --host 127.0.0.1 --port 0",
                       buffering="line")

def before_scenario(context, _):
    context.poll = select.poll()
