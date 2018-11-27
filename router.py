#!/usr/bin/env python3
import argparse
import atexit
import logging
import os
import signal
import socket
import sys

from core import Config, Kapellmeister
from core.routing import Router


def _term(*_):
    exit()


def main(sockname, config_file_name):
    with open(config_file_name) as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()
    be = km.connect("brain")

    sock = socket.socket(socket.AF_UNIX)
    sock.bind(sockname)
    atexit.register(os.unlink, sockname)

    sock.listen()

    router = Router(sock, be)

    while True:
        router.tick()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', required=True)
    parser.add_argument('-c', '--config', default="config.yml")
    args = parser.parse_args()
    main(args.socket, args.config)
