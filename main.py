#!/usr/bin/env python3
import logging
import readline
import sys

from twisted.internet import reactor, stdio

from core import Config, Kapellmeister
from server import ChatProtocol


def main():
    with open("config.yml") as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()
    channel = km.connect("brain")

    stdio.StandardIO(ChatProtocol(channel))
    reactor.run()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    readline.set_auto_history(True)

    main()
