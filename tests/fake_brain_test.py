import json
import socket
import unittest

from core.testing import FakeBrain
from utils import timeout


class FakeBrainConnectTest(unittest.TestCase):

    def setUp(self):
        self._fb = FakeBrain()

    def tearDown(self):
        self._fb.shutdown()

    def test_connect(self):
        self.assertEqual(self._fb.addr[0], '127.0.0.1')
        sock = socket.create_connection(self._fb.addr)

    def test_shutdown(self):
        addr = self._fb.addr

        self._fb.shutdown()

        with self.assertRaises(ConnectionRefusedError):
            socket.create_connection(addr)


class FakeBrainTest(unittest.TestCase):

    def setUp(self):
        self._fb = FakeBrain()
        self._sock = socket.create_connection(self._fb.addr)
        self._fb.work(1)
        self._sock.send(b'{"command": "switch-user", "user": "user"}\n')
        self._fb.work(1)
        self._fb.messages.pop(0)

    def tearDown(self):
        self._fb.shutdown()

    def _send_presence(self, user, channel):
        msg = {'event': 'presence',
               'from': {'user': 'user',
                        'channel': 'channel'}}
        self._sock.send(json.dumps(msg).encode()+b'\n')
        self._fb.work(1)
        return msg

    def test_presence_message(self):
        msg = self._send_presence('user', 'channel')

        self.assertEqual(self._fb.messages, [msg])
        with self.assertRaises(Exception), timeout(0.2):
            self._sock.recv(1024)

    def test_send_message_to(self):
        self._send_presence('user', 'channel')

        self._fb.send_message_to("test", 'user', 'channel')

        with timeout(0.2):
            data = self._sock.recv(1024)
        self.assertTrue(data.endswith(b'\n'))
        msg = json.loads(data.decode().strip())
        self.assertEqual(msg, {"message": "test",
                               "from": {"user": "niege",
                                        "channel": "brain"},
                               "to": {"user": "user",
                                      "channel": 'channel'}})

    def test_echo(self):
        msg = {"message": "test",
               "from": {"user": "user",
                        "channel": 'channel'},
               "to": "brain"}
        self._sock.send(json.dumps(msg).encode()+b'\n')
        self._fb.work(1)

        self.assertEquals(self._fb.messages, [msg])

        with timeout(0.2):
            data = self._sock.recv(1024)
        self.assertTrue(data.endswith(b'\n'))
        msg = json.loads(data.decode().strip())
        self.assertEqual(msg, {"message": "test",
                               "from": "brain",
                               "to": {"user": "user",
                                      "channel": 'channel'}})

    def test_fake_brain_is_line_buffered(self):
        msg = {"message": "test",
               "from": {"user": "user",
                        "channel": 'channel'},
               "to": "brain"}
        self._sock.send(json.dumps(msg).encode()+b'\n')
        self._sock.send(json.dumps(msg).encode()+b'\n')
        self._fb.work(1)

        self.assertEquals(self._fb.messages, [msg, msg])

    def test_fake_brain_ignores_inactive_user(self):
        msg = {"message": "test",
               "from": {"user": "user2",
                        "channel": 'channel'},
               "to": "brain"}
        self._sock.send(json.dumps(msg).encode()+b'\n')
        self._fb.work(1)

        self.assertEqual(self._fb.messages, [msg])
        with self.assertRaises(Exception), timeout(0.2):
            self._sock.recv(1024)
