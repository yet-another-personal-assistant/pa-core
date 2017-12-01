#!/usr/bin/env python3

import argparse
import atexit
import fcntl
import logging
import os
import sys
import time

from dbus.exceptions import DBusException
import notify2
import yaml

from router.routing import Faucet, Router, PipeFaucet, Sink, Rule
from router.routing.runner import Runner

_LOGGER = logging.getLogger(__name__)


class TgFaucet(Faucet):

    def __init__(self, base_faucet):
        super().__init__()
        self._base = base_faucet

    def read(self):
        event = self._base.read()
        if event and 'message' in event:
            message = event['message']
            if 'chat' in message and message['chat'].get('type') == "private":
                message['from']['media'] = 'telegram'
                return message


class TgSink(Sink):

    def __init__(self, base_sink):
        super().__init__()
        self._base = base_sink
        self._logger = logging.getLogger("tg_sink")

    def write(self, message):
        if 'chat_id' in message:
            self._base.write(message)
        else:
            self._logger.warning("No chat_id set for message [%s]",
                                 message['text'])


class StdinFaucet(Faucet):

    def __init__(self):
        super().__init__()
        flags = fcntl.fcntl(0, fcntl.F_GETFL)
        fcntl.fcntl(0, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._file = os.fdopen(0, mode='rb')

    def read(self):
        line = self._file.readline()
        try:
            line = line.decode()
        except UnicodeDecodeError:
            return
        if line:
            return {"from": {"media": "local"}, "text": line}


class StdoutSink(Sink):

    def __init__(self, name):
        super().__init__()
        self._name = name

    def write(self, message):
        print("{}: {}".format(self._name, message['text']))


class TelegramToBrainRule(Rule):

    def __init__(self, tg_users):
        super().__init__(target="brain", media="telegram")
        self._len += 1
        self._tg_users = {**tg_users}

    def target_for(self, message):
        source = message['from']
        if source.get('media') == "telegram" and "id" in source:
            return self._tg_users.get(source['id'])


def make_brain_factory(configs, runner):
    def instantiate_brain(router, brain_name):
        _LOGGER.debug("Checking if we should wake up brain %s", brain_name)
        config = configs.get(brain_name)
        if config:  # it isn't started, that's why we are here
            runner.ensure_running("brain",
                                  alias=brain_name,
                                  with_args=["--socket", brain_name,
                                             "--config", config.filename],
                                  socket=os.path.join("brain", brain_name))
            router.add_sink(runner.get_sink(brain_name), brain_name)
            router.add_faucet(runner.get_faucet(brain_name), brain_name)
    return instantiate_brain


class DumpSink(Sink):

    def write(self, message):
        _LOGGER.debug("Dropped %s", message)


class UserConfig:

    def __init__(self, filename):
        self._filename = os.path.abspath(filename)
        with open(filename) as user_config:
            self._config = yaml.load(user_config)

    @property
    def telegram(self):
        return self._config.get('telegram')

    @property
    def filename(self):
        return self._filename

    @property
    def local(self):
        return self._config.get('local', False)


class NotifierSink(Sink):

    def __init__(self, name):
        super().__init__()
        self._name = name

    def write(self, message):
        notify2.Notification(self._name, message['text']).show()


def add_local_endpoint(router, name, brain_name):
    router.add_faucet(StdinFaucet(), "local")
    router.add_sink(StdoutSink(name), "local")
    router.add_rule(Rule(brain_name), "local")


def add_incoming_faucet(router, brain_name, incoming):
    if os.path.exists(incoming):
        os.unlink(incoming)
    os.mkfifo(incoming)
    incoming_fd = os.open(incoming, os.O_RDONLY | os.O_NONBLOCK)
    atexit.register(lambda: os.unlink(incoming))
    router.add_faucet(PipeFaucet(incoming_fd), "incoming")
    router.add_rule(Rule(brain_name), 'incoming')


def build_router(args):
    router = Router(DumpSink())
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
            if config.local:
                add_local_endpoint(router, args.name, brain_name)
                add_incoming_faucet(router, brain_name, args.incoming)
        configs[brain_name] = config
    router.add_sink_factory(make_brain_factory(configs, runner))
    router.add_rule(TelegramToBrainRule(tg_users), 'telegram')

    runner.ensure_running("telegram", with_args=["--token-file",
                                                 os.path.abspath(args.token)])

    atexit.register(runner.terminate, "telegram")
    router.add_faucet(TgFaucet(runner.get_faucet("telegram")), "telegram")
    router.add_sink(TgSink(runner.get_sink("telegram")), "telegram")

    if not args.no_translator:
        runner.ensure_running("translator")

    try:
        notify2.init("PA")
        router.add_sink(NotifierSink(args.name), "notify")
    except DBusException:
        _LOGGER.error("Failed to initialize notification sink", exc_info=True)

    return router


def main():
    parser = argparse.ArgumentParser(description="Personal assistant core")
    parser.add_argument("--name", default="pa", help="Personal Assistant name")
    parser.add_argument("--token", default="token.txt",
                        help="Telegram token file")
    parser.add_argument("--incoming", default="/tmp/pa_incoming",
                        help="Local incoming pipe")
    parser.add_argument("--users", default="users",
                        help="Path to user configuration files")
    parser.add_argument("--no-translator", default=False, action='store_const',
                        const=True, help="Do not start translator module")
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    logging.getLogger('router').setLevel(logging.DEBUG)
    logging.getLogger('asyncio').setLevel(logging.WARNING)

    args = parser.parse_args()

    router = build_router(args)

    while True:
        router.tick()
        time.sleep(0.2)


if __name__ == '__main__':
    main()
