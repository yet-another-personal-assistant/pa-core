#!/usr/bin/env python3
import argparse
import atexit
import logging
import socket
import sys

from channels import SocketChannel

from core.endpoints import IncomingEndpoint


def main(sockname, pipename):
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(sockname)

    endpoint = IncomingEndpoint(pipename, SocketChannel(sock))
    atexit.register(endpoint.shutdown)

    try:
        while True:
            endpoint.poll(1)
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', required=True)
    parser.add_argument("--pipe", help="named pipe name", default='incoming')
    parser.add_argument("-d", "--debug", action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    main(args.socket, args.pipe)
