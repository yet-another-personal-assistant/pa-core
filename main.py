#!/usr/bin/env python3
import argparse
import atexit
import json
import logging
import select
import signal
import sys

from runner.channel import PipeChannel

from core import Config, Kapellmeister
from core.poller import Poller

_LOGGER = logging.getLogger(__name__)


def _term(*_):
    exit()


def main(config_file):
    with open(config_file) as cfg:
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
                line = data.decode().strip()
                if line:
                    channels['brain'].write(json.dumps({"message": line,
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

    parser = argparse.ArgumentParser(description="Local interface",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    atexit.register(_LOGGER.info, "Exiting")
    main(args.config)
