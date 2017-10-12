#!/usr/bin/env python3

import logging
import subprocess
import sys
import time

from router.routing import Faucet, Router, PipeFaucet, Sink, PipeSink, Rule


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

    def __init__(self, base_sink):
        self._base = base_sink

    def write(self, message):
        if 'chat_id' not in message:
            message['chat_id'] = 43543351
            message['text'] = "Не знаю, кому отправить: {}".format(message['text'])
        super().write(message)


class DumpSink(Sink):

    def __init__(self, logname):
        self._logger = logging.getLogger(logname)

    def write(self, message):
        self._logger.debug("Dropped %s", message)


def main(owner_id):
    logger = logging.getLogger("router")
    tg_proc = subprocess.Popen([".env/bin/python3", "single_stdio.py"],
                               bufsize=1,
                               cwd="tg",
                               stdout=subprocess.PIPE,
                               stdin=subprocess.PIPE)

    faucet = TgFaucet(PipeFaucet(tg_proc.stdout.fileno()))
    router = Router(DumpSink('dumped'))
    router.add_sink(DumpSink('seen'), 'from_me')
    router.add_faucet(faucet, "tg")
    router.add_rule(Rule('from_me', id=owner_id), 'tg')
    while True:
        router.tick()
        time.sleep(1)


if __name__ == '__main__':
    with open('tg/token.txt') as token_file:
        for line in token_file:
            key, value = line.split()
            if key == 'OWNER':
                owner_id = int(value)
                break
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger("dump").setLevel(logging.DEBUG)
    main(owner_id)
