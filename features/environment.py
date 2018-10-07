import select
import shutil

from tempfile import mkdtemp

from runner import Runner

from core.poller import Poller


def before_all(context):
    context.runner = Runner()
    context.runner.add("main", "./main.py", buffering="line")
    context.runner.add("server",
                       command="./server.py --host 127.0.0.1 --port 0",
                       buffering="line")

def before_scenario(context, _):
    context.p = select.poll()
    context.poller = Poller()
    context.dir = mkdtemp()
    context.add_cleanup(shutil.rmtree, context.dir)
    context.fixed_replies = {}
    context.reply_delays = {}
    context.users = {}
