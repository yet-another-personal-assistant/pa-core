import fcntl
import logging
import os
import sys

from router.routing import Faucet, Sink

_LOGGER = logging.getLogger(__name__)


class StdinFaucet(Faucet):

    def __init__(self):
        super().__init__()
        flags = fcntl.fcntl(0, fcntl.F_GETFL)
        fcntl.fcntl(0, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self._file = os.fdopen(0, mode='rb')

    def read(self):
        line = self._file.readline()
        try:
            line = line.decode().rstrip('\n')
        except UnicodeDecodeError:
            _LOGGER.warning("Can't decode line", exc_info=True)
            return
        if line:
            return {"from": {"media": "local"}, "text": line}


class StdoutSink(Sink):

    def __init__(self, name):
        super().__init__()
        self._name = name
        print("> ", end="")
        sys.stdout.flush()

    def write(self, message):
        print("{}: {}".format(self._name, message['text']))
        print("> ", end="")
        sys.stdout.flush()


