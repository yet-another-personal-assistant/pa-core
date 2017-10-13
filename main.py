#!/usr/bin/env python3

import atexit
import logging
import os
import socket
import subprocess
import sys
import time

from router.routing import Faucet, Router, PipeFaucet, Sink, PipeSink, Rule, SocketFaucet, SocketSink


class OldTgFaucet(SocketFaucet):

    def __init__(self, sock, owner_id):
        super().__init__(sock)
        self._owner = owner_id
        sock.send(b'register backend\n')

    def read(self):
        """Almost exact copy of SocketFaucet.read"""
        pos = self._buf.find("\n")
        if pos == -1:
            try:
                data = self._sock.recv(4096).decode()
                if not data:
                    raise EndpointClosedException()
                self._buf += data
            except BlockingIOError:
                pass
            pos = self._buf.find("\n")
        if pos == -1:
            return
        line, self._buf = self._buf[:pos], self._buf[pos+1:]
        if line.startswith("message:"):
            line = line[8:].strip()
        return {"from": {"media": "telegram", "id": self._owner},
                "text": line}

    @staticmethod
    def factory(owner_id):
        return lambda sock: OldTgFaucet(sock, owner_id)


class OldTgSink(SocketSink):

    def write(self, message):
        """Almost exact copy of SocketSink.write"""
        try:
            self._sock.send("message: {}\n".format(message['text']).encode())
        except BrokenPipeError:
            raise EndpointClosedException()


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
                 sink_factory=SocketSink):
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
    sock.connect(sock_path)
    router.add_sink(SocketSink(sock), endpoint_name)
    router.add_faucet(SocketFaucet(sock), endpoint_name)


def main(owner_id, sock_name, friends):
    logger = logging.getLogger("router")
    router = Router(DumpSink('dumped'))
    router.add_sink(DumpSink('seen'), 'from_me')

    if True:
        tg_proc = subprocess.Popen([".env/bin/python3", "single_stdio.py"],
                                   cwd="tg",
                                   stdout=subprocess.PIPE,
                                   stdin=subprocess.PIPE)

        atexit.register(tg_proc.terminate)
        router.add_faucet(TgFaucet(PipeFaucet(tg_proc.stdout.fileno())), "tg")
        router.add_sink(TgSink(PipeSink(tg_proc.stdin.fileno()), owner_id), "tg")
    else:
        add_endpoint(router, "tg",
                     command=[".env/bin/python3", "pa.py", "--no-greet"],
                     cwd="tg",
                     sock_path=sock_name,
                     faucet_factory=OldTgFaucet.factory(owner_id),
                     sink_factory=OldTgSink)

    for user in (owner_id, *friends):
        endpoint_name = "brain{}".format(user)
        socket_name = "socket{}".format(user)
        add_endpoint(router, endpoint_name,
                     command=["sbcl", "--script", "run.lisp", "--socket", socket_name, "--tg-owner", str(user)],
                     cwd="brain",
                     sock_path=socket_name)
        router.add_rule(Rule("tg"), endpoint_name)
        router.add_rule(Rule(endpoint_name, id=user), 'tg')
    while True:
        router.tick()
        time.sleep(0.2)


if __name__ == '__main__':
    sock_name = "socket"
    friends = []
    with open('tg/token.txt') as token_file:
        for line in token_file:
            key, value = line.split()
            if key == 'OWNER':
                owner_id = int(value)
            elif key == 'SOCKET':
                sock_name = value.strip()
            elif key == 'FRIEND':
                friends.append(int(value))
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger("dump").setLevel(logging.DEBUG)
    main(owner_id, sock_name, friends)
