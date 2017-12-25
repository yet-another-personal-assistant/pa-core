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
from tg import init_tg, TgFaucet, TgSink, TelegramToBrainRule

_LOGGER = logging.getLogger(__name__)


def make_brain_factory(configs, runner, args):
    def instantiate_brain(router, brain_name):
        _LOGGER.debug("Checking if we should wake up brain %s", brain_name)
        config = configs.get(brain_name)
        if config:  # it isn't started, that's why we are here
            sock_path = os.path.join(args.brains, brain_name)
            saved_path = os.path.join(args.brains, config.user_name)
            runner.ensure_running("brain",
                                  alias=brain_name,
                                  with_args=["--socket", sock_path,
                                             "--config", config.filename,
                                             "--saved", saved_path],
                                  socket=sock_path)
            router.add_sink(runner.get_sink(brain_name), brain_name)
            router.add_faucet(runner.get_faucet(brain_name), brain_name)
            atexit.register(runner.terminate, brain_name)
    return instantiate_brain


class DumpSink(Sink):

    def write(self, message):
        _LOGGER.debug("Dropped %s", message)

    def close(self):
        pass


class UserConfig:

    def __init__(self, user_name, filename):
        self._filename = os.path.abspath(filename)
        self._user_name = user_name
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

    @property
    def user_name(self):
        return self._user_name


class NotifierSink(Sink):

    def __init__(self, name):
        super().__init__()
        self._name = name

    def write(self, message):
        notify2.Notification(self._name, message['text']).show()

    def close(self):
        pass


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
    bot = init_tg(args.token)
    router.add_faucet(TgFaucet(bot), "telegram")
    router.add_sink(TgSink(bot), "telegram")


def load_configs(router, args):
    configs = {}
    for num, user_file_name in enumerate(os.listdir(args.users)):
        brain_name = 'brain{}'.format(num)
        if not user_file_name.endswith(".yml"):
            continue
        user_name = user_file_name[:-4]
        file_path = os.path.join(args.users, user_file_name)
        config = UserConfig(user_name, file_path)
        if config.local:
            bind_stdio_to_brain(router, brain_name)
        if config.incoming is not None:
            add_incoming_faucet(router, brain_name, config.incoming)
        configs[brain_name] = config
    return configs


def build_router(args):
    router = Router(DumpSink())
    runner = Runner()
    runner.load("modules.yml")

    configs = load_configs(router, args)
    router.add_sink_factory(make_brain_factory(configs, runner, args))

    tg_users = {}
    for name, config in configs.items():
        if config.telegram is not None:
            tg_users[config.telegram] = name

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
    args.brains = os.path.abspath(config.get('brains', './_brains'))
    if not os.path.exists(args.brains):
        os.mkdir(args.brains)

    debug = config.get('debug', {})
    for module, log_level in _LOG_LEVELS_DEFAULT.items():
        level = debug.get(module, log_level)
        logging.getLogger(module).setLevel(_LOG_LEVELS[level])

    logging.getLogger('urllib3').setLevel(logging.INFO)

    logging.basicConfig(stream=sys.stderr,
                        level=_LOG_LEVELS[debug.get('default', 'debug')])

    router = build_router(args)

    try:
        while True:
            router.tick()
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
