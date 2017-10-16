#!/usr/bin/env python3

import atexit
import logging
import os
import socket
import subprocess
import sys
import time

from router.routing import Faucet, Router, PipeFaucet, Sink, PipeSink, Rule, SocketFaucet, SocketSink


class TgFaucet(Faucet):

    def __init__(self, base_faucet):
        self._base = base_faucet

    def read(self):
        event = self._base.read()
        if event and 'message' in event:
            message = event['message']
            message['from']['media'] = 'telegram'
            return message


class TgSink(Sink):

    def __init__(self, base_sink, owner_id):
        self._base = base_sink
        self._owner = owner_id

    def write(self, message):
        if 'chat_id' not in message:
            message['chat_id'] = owner_id
            message['text'] = "Не знаю, кому отправить: {}".format(message['text'])
        self._base.write(message)


class DumpSink(Sink):

    def __init__(self, logname):
        self._logger = logging.getLogger(logname)

    def write(self, message):
        self._logger.debug("Dropped %s", message)


def add_endpoint(router, endpoint_name, command, cwd, sock_path,
                 faucet_factory=SocketFaucet,
                 sink_factory=SocketSink,
                 just_start=False):
    if not os.path.isabs(sock_path):
        sock_path = os.path.join(cwd, sock_path)
    if os.path.exists(sock_path):
        os.unlink(sock_path)
    proc = subprocess.Popen(command, cwd=cwd)
    atexit.register(proc.terminate)

    sock = socket.socket(socket.AF_UNIX)
    logging.getLogger("main").info("connecting to %s for endpoint %s", sock_path, endpoint_name)
    while not os.path.exists(sock_path):
        time.sleep(1)
    if not just_start:
        sock.connect(sock_path)
        router.add_sink(SocketSink(sock), endpoint_name)
        router.add_faucet(SocketFaucet(sock), endpoint_name)


def main(owner_id, args, friends):
    logger = logging.getLogger("router")
    router = Router(DumpSink('dumped'))
    router.add_sink(DumpSink('seen'), 'from_me')

    incoming = args.incoming
    if os.path.exists(incoming):
        os.unlink(incoming)
    os.mkfifo(incoming)
    incoming_fd = os.open(incoming, os.O_RDONLY | os.O_NONBLOCK)
    atexit.register(lambda: os.unlink(incoming))
    router.add_faucet(PipeFaucet(incoming_fd), "incoming")

    tg_proc = subprocess.Popen([".env/bin/python3", "single_stdio.py",
                                "--token-file", os.path.abspath(args.token)],
                                cwd="tg",
                                stdout=subprocess.PIPE,
                                stdin=subprocess.PIPE)

    atexit.register(tg_proc.terminate)
    router.add_faucet(TgFaucet(PipeFaucet(tg_proc.stdout.fileno())), "tg")
    router.add_sink(TgSink(PipeSink(tg_proc.stdin.fileno()), owner_id), "tg")

    add_endpoint(router, "pa2human",
                 command=[".env/bin/python3", "translator.py"],
                 cwd="pa2human",
                 sock_path="/tmp/tr_socket",
                 just_start=True)

    for user in (owner_id, *friends):
        endpoint_name = "brain{}".format(user)
        socket_name = "socket{}".format(user)
        add_endpoint(router, endpoint_name,
                     command=["sbcl", "--script", "run.lisp",
                              "--socket", socket_name,
                              "--tg-owner", str(user)],
                     cwd="brain",
                     sock_path=socket_name)
        router.add_rule(Rule("tg"), endpoint_name)
        router.add_rule(Rule(endpoint_name, id=user), 'tg')

    router.add_rule(Rule("brain{}".format(owner_id)), 'incoming')
    while True:
        router.tick()
        time.sleep(0.2)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Personal assistant message router")
    parser.add_argument("--token", default="token.txt", help="Telegram token file")
    parser.add_argument("--incoming", default="/tmp/pa_incoming", help="Local incoming pipe")
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger('router').setLevel(logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    args = parser.parse_args()
    friends = []

    with open(args.token) as token_file:
        for line in token_file:
            key, value = line.split()
            if key == 'OWNER':
                owner_id = int(value)
            elif key == 'FRIEND':
                friends.append(int(value))
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger("dump").setLevel(logging.DEBUG)
    main(owner_id, args, friends)
