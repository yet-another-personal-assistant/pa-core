#!/usr/bin/env python3
import argparse
import logging
import sys

from twisted.internet import reactor

from core import Config, Kapellmeister
from server import ChatProtocolFactory


def main(addr, port):
    with open("config.yml") as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()
    channel = km.connect("brain")

    listening = reactor.listenTCP(port,
                                  ChatProtocolFactory(channel),
                                  interface=addr)
    addr = listening.getHost()
    print("Server started on", addr.host+':'+str(addr.port))
    sys.stdout.flush()
    reactor.run()


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="pa-server",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="host to bind to", default='0.0.0.0')
    parser.add_argument("--port", type=int, help="port to use", default=8001)
    args = parser.parse_args()

    main(args.host, args.port)
