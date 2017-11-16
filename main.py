#!/usr/bin/env python3

import atexit
import logging
import os
import sys
import time
import yaml

from router.routing import Faucet, Router, PipeFaucet, Sink, PipeSink, Rule, SocketFaucet, SocketSink
from router.routing.runner import Runner


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
        self._logger = logging.getLogger("tg_sink")

    def write(self, message):
        if 'chat_id' in message:
            self._base.write(message)
        else:
            self._logger.warning("No chat_id set for message [%s]", message['text'])


class TelegramToBrainRule(Rule):

    def __init__(self, tg_users):
        base = super(TelegramToBrainRule, self)
        base.__init__(target="brain", media="telegram")
        self._len += 1
        self._tg_users = {**tg_users}

    def target_for(self, message):
        source = message['from']
        if source.get('media') == "telegram" and "id" in source:
            return self._tg_users.get(source['id'])


def make_brain_factory(configs, runner):
    def instantiate_brain(router, brain_name):
        logging.getLogger("brain factory").debug("Checking if we should wake up brain %s",
                                                brain_name)
        if brain_name in configs: # it isn't started, that's why we are here
            runner.ensure_running("brain",
                                  alias=brain_name,
                                  with_args=["--socket", brain_name,
                                             "--config", configs[brain_name].file],
                                  socket=os.path.join("brain", brain_name))
            router.add_sink(runner.get_sink(brain_name), brain_name)
            router.add_faucet(runner.get_faucet(brain_name), brain_name)
    return instantiate_brain


class DumpSink(Sink):

    def __init__(self, logname):
        self._logger = logging.getLogger(logname)

    def write(self, message):
        self._logger.debug("Dropped %s", message)


class UserConfig:

    def __init__(self, filename):
        self._filename = os.path.abspath(filename)
        with open(filename) as user_config:
            self._config = yaml.load(user_config)

    @property
    def telegram(self):
        return self._config.get('telegram')

    @property
    def file(self):
        return self._filename


class MyRouter(Router):

    def __init__(self):
        super().__init__(DumpSink('dumped'))


def main(owner_id, args, friends):
    router = MyRouter()
    runner = Runner()
    runner.load("modules.yml")

    tg_users = {}
    configs = {}
    for num, user_file_name in enumerate(os.listdir(args.users)):
        brain_name = 'brain{}'.format(num)
        if not user_file_name.endswith(".yml"):
            continue
        file_path = os.path.join(args.users, user_file_name)
        config = UserConfig(file_path)
        if config.telegram is not None:
            tg_users[config.telegram] = brain_name
            if config.telegram == owner_id:
                owner_brain = brain_name
        configs[brain_name] = config
    router.add_sink_factory(make_brain_factory(configs, runner))
    router.add_rule(TelegramToBrainRule(tg_users), 'telegram')

    incoming = args.incoming
    if os.path.exists(incoming):
        os.unlink(incoming)
    os.mkfifo(incoming)
    incoming_fd = os.open(incoming, os.O_RDONLY | os.O_NONBLOCK)
    atexit.register(lambda: os.unlink(incoming))
    router.add_faucet(PipeFaucet(incoming_fd), "incoming")

    runner.ensure_running("telegram", with_args=["--token-file",
                                                 os.path.abspath(args.token)])

    atexit.register(runner.terminate, "telegram")
    router.add_faucet(TgFaucet(runner.get_faucet("telegram")), "telegram")
    router.add_sink(TgSink(runner.get_sink("telegram")), "telegram")

    if not args.no_translator:
        runner.ensure_running("translator")

    router.add_rule(Rule(owner_brain), 'incoming')

    while True:
        router.tick()
        time.sleep(0.2)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Personal assistant message router")
    parser.add_argument("--token", default="token.txt", help="Telegram token file")
    parser.add_argument("--incoming", default="/tmp/pa_incoming", help="Local incoming pipe")
    parser.add_argument("--users", default="users", help="Path to user configuration files")
    parser.add_argument("--no-translator", default=False, action='store_const',
                        const=True, help="Do not start translator module")
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
