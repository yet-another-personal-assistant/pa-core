#!/usr/bin/env python3

import json
import logging
import readline
import signal
import sys

from core import Config, Kapellmeister
from utils import timeout


_LOGGER = logging.getLogger(__name__)


def _await_reply(channel):
    result = b''
    with timeout(1):
        while not result:
            result = channel.read()
    return result


# FIXME
def stop_all(km):
    _LOGGER.warn("stop all")


def mainloop(km):
    channel = km.connect("brain")

    while True:
        s = input("> ")
        channel.write(json.dumps({"message": s,
                                  "from": {"user": "user",
                                           "channel": "channel"},
                                  "to": {"user": "niege",
                                         "channel": "brain"}}).encode())
        result = _await_reply(channel).decode()
        print("Niege>", json.loads(result)['message'])


def _term(*_):
    exit()


def main():
    with open("config.yml") as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()

    try:
        mainloop(km)
    except KeyboardInterrupt:
        _LOGGER.info("Exiting on keyboard interrupt")


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    readline.set_auto_history(True)

    main()
