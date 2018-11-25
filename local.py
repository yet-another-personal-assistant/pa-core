#!/usr/bin/env python3
import argparse
import getpass
import json
import logging
import socket
import sys

from channels import PipeChannel, SocketChannel
from channels.poller import Poller

from utils import timeout


_LOGGER = logging.getLogger(__name__)

_POLLER = Poller()
_STDIO = None
_ROUTER = None
_USER = getpass.getuser()
_CHANNEL = 'local:'+socket.gethostname()


def set_stdio(channel):
    global _STDIO
    if _STDIO is not None:
        _POLLER.unregister(_STDIO)
    _STDIO = channel
    if _STDIO is not None:
        _POLLER.register(_STDIO)


def set_router(channel):
    global _ROUTER
    if _ROUTER is not None:
        _POLLER.unregister(_ROUTER)
    _ROUTER = channel
    if _ROUTER is not None:
        _POLLER.register(_ROUTER)


def send_name():
    _ROUTER.write(b'local\n')


def poll(timeout=None):
    for data, channel in _POLLER.poll(timeout):
        if channel == _STDIO:
            if not data:
                exit(0)
            line = data.decode('utf-8', 'ignore').strip()
            if not line:
                continue
            msg = {"message": line,
                   "from": {"user": _USER,
                            "channel": _CHANNEL},
                   "to": {"user": "niege",
                          "channel": "brain"}}
            _ROUTER.write(json.dumps(msg).encode(), b'\n')
        else:
            if not data:
                _STDIO.write(b"Connection closed\n")
                exit(0)
            msg = json.loads(data.decode())
            _STDIO.write(b'Niege> ', msg['message'].encode(), b'\n')


def main(sockname):
    sock = socket.socket(socket.AF_UNIX)
    sock.connect(sockname)
    set_router(SocketChannel(sock, buffering='line'))
    set_stdio(PipeChannel(sys.stdin.fileno(),
                          sys.stdout.fileno(),
                          buffering='line'))
    send_name()

    try:
        while True:
            poll()
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    #logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--socket', required=True)
    args = parser.parse_args()
    main(args.socket)
