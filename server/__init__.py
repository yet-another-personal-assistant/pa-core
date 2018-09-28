import json
import logging

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from utils import timeout


_LOGGER = logging.getLogger(__name__)


def _await_reply(channel):
    result = b''
    with timeout(1):
        while not result:
            result = channel.read()
    return result


class ChatProtocol(LineReceiver):
    delimiter = b'\n'

    def __init__(self, channel):
        self._channel = channel

    def connectionMade(self):
        self.transport.setTcpNoDelay(True)
    
    def lineReceived(self, line):
        self._channel.write(json.dumps({"message": line.decode(),
                                        "from": {"user": "user",
                                                 "channel": "channel"},
                                        "to": {"user": "niege",
                                               "channel": "brain"}}).encode())
        
        result = _await_reply(self._channel).decode()
        _LOGGER.debug("Sending")
        self.transport.write(b'Niege> ')
        self.transport.write(json.loads(result)['message'].encode())
        self.transport.write(b'\n')
        #self.sendLine(b'Niege> '+json.loads(result)['message'].encode())
        _LOGGER.debug("Sent")


class ChatProtocolFactory(Factory):

    def __init__(self, channel):
        self._channel = channel

    def buildProtocol(self, _):
        return ChatProtocol(self._channel)
