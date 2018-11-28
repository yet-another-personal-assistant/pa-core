#!/usr/bin/env python3
import argparse
import atexit
import logging
import os
import signal
import socket
import sys

from tempfile import gettempdir

from runner import Runner

import tcp

_LOGGER = logging.getLogger(__name__)


def _term(*_):
    exit()


def main(host, port, config):
    runner = Runner()

    sockname = os.path.join(gettempdir(),
                            "router_{}_socket".format(os.getpid()))
    runner.add("router", "./router.py",
               type="socket", socket=sockname)
    atexit.register(runner.terminate, "router")
    runner.ensure_running("router",
                          with_args=["--socket", sockname,
                                     "--config", config])

    tcp.main(sockname, host, port, config)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)

    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="pa-server",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="host to bind to", default='0.0.0.0')
    parser.add_argument("--port", type=int, help="port to use", default=8001)
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    main(args.host, args.port, args.config)
