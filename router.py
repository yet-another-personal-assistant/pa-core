#!/usr/bin/env python3
import argparse
import atexit
import logging
import os
import signal
import socket
import sys

from channels import SocketChannel

from core.routing import Router


def _term(*_):
    exit()


def start_server(sockname):
    if ':' in sockname:
        host, port = sockname.split(':')
        serv = socket.socket(socket.AF_INET)
        serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        serv.bind((host, int(port)))
        sockname = serv.getsockname()
        sys.stdout.flush()
    else:
        serv = socket.socket(socket.AF_UNIX)
        serv.bind(sockname)
        atexit.register(os.unlink, sockname)
    serv.listen(0)
    return serv, sockname


def main(sockname, config_file_name, brain_sockname):
    brain_serv, brain_serv_addr = start_server(brain_sockname)

    be = SocketChannel(brain_serv.accept()[0])

    sock, router_addr = start_server(sockname)
    router = Router(sock, be)

    while True:
        router.tick()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', required=True)
    parser.add_argument('-b', '--brain-socket', default="0.0.0.0:0")
    parser.add_argument('-c', '--config', default="config.yml")
    args = parser.parse_args()
    main(args.socket, args.config, args.brain_socket)
