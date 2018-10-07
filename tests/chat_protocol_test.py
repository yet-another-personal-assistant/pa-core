import json
import signal
import time
import unittest

from twisted.internet.protocol import Factory
from twisted.test.proto_helpers import StringTransportWithDisconnection
from twisted.trial.unittest import TestCase

from server import ChatProtocol, ChatProtocolFactory
from runner.channel import Channel


class MockChannel(Channel):

    to_read = []
    to_write = []

    def read(self):
        if self.to_read:
            return self.to_read.pop()
        return 

    def write(self, *data):
        self.to_write.extend(data)

    def close(self):
        pass


class MockFactory(Factory):
    pass


def with_delay(timeout, action, *args, **kwargs):
    def handler(signum, flame):
        action(*args, **kwargs)
    signal.signal(signal.SIGALRM, with_delay)
    signal.setitimer(signal.ITIMER_REAL, timeout)


class TestChatProtocol(TestCase):

    def setUp(self):
        self.channel = MockChannel()
        self.sp = ChatProtocol(self.channel)
        self.transport = StringTransportWithDisconnection()
        self.sp.makeConnection(self.transport)
        self.transport.protocol = self.sp
        self.sp.factory = MockFactory()

    def test_prompt(self):
        self.assertEquals(self.transport.value(), b'')

    def test_message_sent_to_brain(self):
        self.channel.to_read.append(b'{"message": ""}')
        self.sp.dataReceived(b'Hello\n')
        line = self.channel.to_write[0].decode()

        self.assertEquals(json.loads(line),
                          {"message": "Hello",
                           "from": {"user": "user", "channel": "channel"},
                           "to": {"user": "niege", "channel": "brain"}})

    def test_print_result_from_brain(self):
        brain_reply = json.dumps({"message": "Hi",
                                  "from": {"user": "niege",
                                           "channel": "channel"},
                                  "to": {"user": "user",
                                         "channel": "channel"}})
        self.channel.to_read.append(brain_reply.encode())
        self.sp.dataReceived(b'Hello\n')

        self.assertEquals(self.transport.value(),
                          b'Niege> Hi\n')

    def test_wait_for_brain_answer(self):
        brain_reply = json.dumps({"message": "Hi",
                                  "from": {"user": "niege",
                                           "channel": "channel"},
                                  "to": {"user": "user",
                                         "channel": "channel"}})
        self.channel.to_read.extend([b'']*10)
        self.channel.to_read.append(brain_reply.encode())
        self.sp.dataReceived(b'Hello\n')

        self.assertEquals(self.transport.value(),
                          b'Niege> Hi\n')

    def test_no_answer(self):
        self.channel.read = lambda self: time.sleep(3)

        self.sp.dataReceived(b'Hello\n')

        self.assertEquals(self.transport.value(),
                          b'')


class ChatProtocolFactoryTest(unittest.TestCase):

    def setUp(self):
        self.channel = MockChannel()
        self.factory = ChatProtocolFactory(self.channel)

    def test_create_protocol(self):
        self.factory.buildProtocol(None)
