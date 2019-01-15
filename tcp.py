#!/usr/bin/env python3
import argparse
import logging
import socket
import sys
import time

from channels import SocketChannel

from core.endpoints import TcpEndpoint


def main(sockname, host, port):
    serv = socket.socket()
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    serv.bind((host, port))
    addr, port = serv.getsockname()
    serv.listen(0)

    if ':' in sockname:
        rhost, rport = sockname.split(':')
        while True:
            try:
                sock = socket.create_connection((rhost, int(rport)))
                break
            except ConnectionRefusedError:
                time.sleep(0.1)
    else:
        sock = socket.socket(socket.AF_UNIX)
        sock.connect(sockname)

    endpoint = TcpEndpoint(serv, SocketChannel(sock))
    endpoint.send_name()

    print("Server started on", addr+':'+str(port))
    sys.stdout.flush()
    try:
        while True:
            endpoint.poll(1)
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', required=True)
    parser.add_argument("--host", help="host to bind to", default='0.0.0.0')
    parser.add_argument("--port", type=int, help="port to use", default=8001)
    parser.add_argument("-d", "--debug", action='store_true')
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    main(args.socket, args.host, args.port)
