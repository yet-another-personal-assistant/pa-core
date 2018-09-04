import json

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

from utils import timeout


def _await_reply(channel):
    result = b''
    with timeout(1):
        while not result:
            result = channel.read()
    return result


class ChatProtocol(LineReceiver):
    def __init__(self, channel):
        self._channel = channel

    def _sendPrompt(self):
        self.delimiter = b' '
        self.sendLine(b'>')
        self.delimiter = b'\n'

    def connectionMade(self):
        self._sendPrompt()

    
    def lineReceived(self, line):
        self._channel.write(json.dumps({"message": line.decode(),
                                        "from": {"user": "user",
                                                 "channel": "channel"},
                                        "to": {"user": "niege",
                                               "channel": "brain"}}).encode())
        
        result = _await_reply(self._channel)
        self.sendLine(b'Niege> '+json.loads(result)['message'].encode())
        self._sendPrompt()


class ChatProtocolFactory(Factory):

    def __init__(self, channel):
        self._channel = channel

    def buildProtocol(self, _):
        return ChatProtocol(self._channel)
