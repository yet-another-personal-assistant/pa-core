#!/usr/bin/env python3

import argparse
import atexit
import logging
import os
import sys
import time

from dbus.exceptions import DBusException
import notify2
import yaml

from router.routing import Router, PipeFaucet, Sink, Rule
from router.routing.runner import Runner
from stdio import StdinFaucet, StdoutSink
from tg import TgFaucet, TgSink, TelegramToBrainRule

_LOGGER = logging.getLogger(__name__)


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

    @property
    def incoming(self):
        return self._config.get('incoming')


class NotifierSink(Sink):

    def __init__(self, name):
        super().__init__()
        self._name = name

    def write(self, message):
        notify2.Notification(self._name, message['text']).show()


def add_stdio_endpoint(router, name):
    router.add_faucet(StdinFaucet(), "local")
    router.add_sink(StdoutSink(name), "local")


def bind_stdio_to_brain(router, brain_name):
    router.add_rule(Rule(brain_name), "local")


def add_incoming_faucet(router, brain_name, incoming):
    if os.path.exists(incoming):
        os.unlink(incoming)
    os.mkfifo(incoming)
    incoming_fd = os.open(incoming, os.O_RDONLY | os.O_NONBLOCK)
    atexit.register(lambda: os.unlink(incoming))
    router.add_faucet(PipeFaucet(incoming_fd), "incoming")
    router.add_rule(Rule(brain_name), 'incoming')


def add_tg_endpoint(router, runner, tg_users, args):
    router.add_rule(TelegramToBrainRule(tg_users), 'telegram')
    runner.ensure_running("telegram", with_args=["--token", args.token])

    atexit.register(runner.terminate, "telegram")
    router.add_faucet(TgFaucet(runner.get_faucet("telegram")), "telegram")
    router.add_sink(TgSink(runner.get_sink("telegram")), "telegram")


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
            bind_stdio_to_brain(router, brain_name)
        if config.incoming is not None:
            add_incoming_faucet(router, brain_name, config.incoming)
        configs[brain_name] = config
    router.add_sink_factory(make_brain_factory(configs, runner))

    if args.token is not None:
        add_tg_endpoint(router, runner, tg_users, args)
    add_stdio_endpoint(router, args.name)

    if args.translator:
        runner.ensure_running("translator")
    else:
        _LOGGER.info("Not starting translator")

    if args.notifications:
        try:
            notify2.init("PA")
            router.add_sink(NotifierSink(args.name), "notify")
        except DBusException:
            _LOGGER.error("Failed to initialize notification sink", exc_info=True)
    else:
        _LOGGER.info("Not showing notifications")

    return router


_LOG_LEVELS = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'notset': logging.NOTSET,
}

_LOG_LEVELS_DEFAULT = {
    'router': 'debug',
    'asyncio': 'warning',
}


def main():
    parser = argparse.ArgumentParser(description="Personal assistant core")
    parser.add_argument("--users", default="users",
                        help="Path to user configuration files")
    parser.add_argument("--config", default="default.yml", help="Bot configuration file")

    args = parser.parse_args()
    _LOGGER.info("Using config %s", args.config)
    with open(args.config) as config_file:
        config = yaml.load(config_file)
    args.token = config.get('telegram')
    args.name = config.get('name')
    args.translator = config.get('translator')
    args.notifications = config.get('notify')

    debug = config.get('debug', {})
    for module, log_level in _LOG_LEVELS_DEFAULT.items():
        level = debug.get(module, log_level)
        logging.getLogger(module).setLevel(_LOG_LEVELS[level])

    logging.basicConfig(stream=sys.stderr,
                        level=_LOG_LEVELS[debug.get('default', 'debug')])

    router = build_router(args)

    while True:
        router.tick()
        time.sleep(0.2)


if __name__ == '__main__':
    main()
