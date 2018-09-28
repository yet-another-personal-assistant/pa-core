#!/usr/bin/env python3
import atexit
import json
import logging
import readline
import select
import signal
import sys

from core import Config, Kapellmeister

_LOGGER = logging.getLogger(__name__)


def _term(*_):
    exit()


def main():
    with open("config.yml") as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()
    channel = km.connect("brain")

    poll = select.poll()
    fds = {
        sys.stdin.fileno(): "stdin",
        channel.get_fd(): "chan",
    }
    for fd in fds:
        poll.register(fd, select.POLLIN | select.POLLERR | select.POLLHUP)
        _LOGGER.debug("Registered fd %d", fd)

    while True:
        for fd, event in poll.poll():
            _LOGGER.debug("Event %d on fd %d", event, fd)
            name = fds[fd]
            if name == 'stdin':
                if event & select.POLLIN:
                    line = sys.stdin.readline()
                    channel.write(json.dumps({"message": line.strip(),
                                              "from": {"user": "user",
                                                       "channel": "channel"},
                                              "to": {"user": "niege",
                                                     "channel": "brain"}}).encode())
                if event & (select.POLLERR | select.POLLHUP):
                    return
            elif name == 'chan':
                line = channel.read()
                _LOGGER.info("XXX %s XXX", line)
                msg = json.loads(line)
                _LOGGER.info("MMM %s", msg)
                print("Niege>", msg['message'])
                sys.stdout.flush()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
    readline.set_auto_history(True)

    atexit.register(_LOGGER.info, "Exiting")
    main()
