import os
import select
import shutil

from tempfile import mkdtemp

from runner import Runner

from core.testing import FakeBrain



def before_all(context):
    context.runner = Runner()
    context.runner.add("main", "./main.py", buffering="line")
    context.runner.add("server",
                       command="./server.py --host 127.0.0.1 --port 0",
                       buffering="line")

def before_scenario(context, _):
    context.dir = mkdtemp()
    context.add_cleanup(shutil.rmtree, context.dir)
    context.p = select.poll()
    context.b = FakeBrain()
    if 'fake' in context.tags:
        with open(os.path.join(context.dir, "config.yml"), "w") as cfg:
            cfg.write("""components:\n  brain:
    command: socat STDIO TCP:{}:{}
    buffering: line""".format(*context.b.addr))
