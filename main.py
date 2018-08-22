#!/usr/bin/env python3

import atexit
import json
import logging
import os
import readline
import shutil
import signal
import sys

from tempfile import mkdtemp

from runner import Runner

from utils import timeout


_LOGGER = logging.getLogger(__name__)


def _await_reply(channel):
    result = b''
    with timeout(1):
        while not result:
            result = channel.read()
    return result


def stop_all(runner):
    runner.get_channel("brain").close()
    runner.terminate("brain")
    runner.terminate("translator")


def mainloop(runner):
    channel = runner.get_channel("brain")

    while True:
        print("> ", end='', flush=True)
        s = sys.stdin.readline()
        channel.write(json.dumps({"message": s.strip(),
                                "from": {"user": "user", "channel": "channel"},
                                "to": {"user": "niege", "channel": "brain"}}).encode())
        result = _await_reply(channel).decode()
        print("Niege>", json.loads(result)['message'])


def _term(*_):
    exit()


def main():
    tmpdir = mkdtemp()
    atexit.register(shutil.rmtree, tmpdir)
    translator_socket = os.path.join(tmpdir, "tr")

    runner = Runner()
    runner.add("brain", "sbcl --script run.lisp",
               cwd="brain", buffering="line", setpgrp=True)
    runner.add("translator", "./pa2human.py",
               cwd="pa2human", type="socket")

    atexit.register(lambda: stop_all(runner))
    runner.start("translator",
                 with_args=["--socket", translator_socket],
                 socket=translator_socket)
    runner.start("brain",
                 with_args=["--translator", translator_socket])

    try:
        mainloop(runner)
    except KeyboardInterrupt:
        _LOGGER.info("Exiting on keyboard interrupt")


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    readline.set_auto_history(True)

    main()
