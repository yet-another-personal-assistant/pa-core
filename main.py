#!/usr/bin/env python3
import atexit
import json
import logging
import readline
import select
import signal
import sys

from runner.channel import PipeChannel

from core import Config, Kapellmeister
from core.poller import Poller

_LOGGER = logging.getLogger(__name__)


def _term(*_):
    exit()


def main():
    with open("config.yml") as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()

    poller = Poller()
    channels = {
        "stdio": PipeChannel(sys.stdin.fileno(), sys.stdout.fileno()),
        "brain": km.connect("brain"),
    }
    channel_names = dict((v,k) for k,v in channels.items())
    for chan in channels.values():
        poller.register(chan)

    while True:
        for data, channel in poller.poll():
            name = channel_names[channel]
            if name == 'stdio':
                line = data.decode()
                channels['brain'].write(json.dumps({"message": line.strip(),
                                                    "from": {"user": "user",
                                                             "channel": "channel"},
                                                    "to": {"user": "niege",
                                                           "channel": "brain"}}).encode())
            elif name == 'brain':
                _LOGGER.info("XXX %s XXX", data)
                msg = json.loads(data)
                _LOGGER.info("MMM %s", msg)
                channels['stdio'].write(b"Niege> ", msg['message'].encode(), b'\n')
            else:
                _LOGGER.error("Unknown channel %s", channel)
                exit(-1)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    readline.set_auto_history(True)

    atexit.register(_LOGGER.info, "Exiting")
    main()
