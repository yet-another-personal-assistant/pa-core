#!/usr/bin/env python3

import atexit
import json
import logging
import sys

from runner import Runner

from utils import timeout


_LOGGER = logging.getLogger(__name__)


def _await_reply(channel):
    result = b''
    with timeout(1):
        while not result:
            result = channel.read()
    return result


def stop_brain(runner):
    runner.get_channel("brain").close()
    runner.terminate("brain")


def main():
    runner = Runner()
    runner.add("brain", "sbcl --script run.lisp",
               cwd="brain", buffering="line", setpgrp=True)
    atexit.register(lambda: stop_brain(runner))
    runner.start("brain")
    channel = runner.get_channel("brain")

    try:
        while True:
            print("> ", end='', flush=True)
            s = sys.stdin.readline()
            channel.write(json.dumps({"message": s.strip(),
                                    "from": {"user": "user", "channel": "channel"},
                                    "to": {"user": "niege", "channel": "brain"}}).encode())
            result = _await_reply(channel).decode()
            print("Niege>", json.loads(result)['message'])
    except KeyboardInterrupt:
        _LOGGER.info("Exiting on keyboard interrupt")


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    main()
