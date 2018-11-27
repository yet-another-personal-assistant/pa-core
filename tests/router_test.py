import json
import select
import socket
import shutil
import unittest

from tempfile import mkdtemp

from channels import SocketChannel

from core.routing import Router
from core.testing import FakeBrain


class RouterTest(unittest.TestCase):

    def setUp(self):
        self.sock = socket.socket(socket.AF_INET)
        self.sock.bind(('0.0.0.0', 0))
        self.addr = self.sock.getsockname()
        self.sock.listen()

        self.fb = FakeBrain()
        sock = socket.create_connection(self.fb.addr)
        self.fb.work(0.01)
        self.be = SocketChannel(sock, buffering='line')

        self.router = Router(self.sock, self.be)

    def tearDown(self):
        self.fb.shutdown()
        self.be.close()
        self.sock.close()

    def _connect(self, channel_name="channel"):
        client = socket.create_connection(self.addr)
        self.addCleanup(client.close)
        self.router.tick(0.01)
        client.send(channel_name.encode()+b'\n')
        self.router.tick(0.01)
        return client

    def _feed(self, client, msg):
        client.send(json.dumps(msg).encode()+b'\n')
        self.router.tick(0.01)
        self.fb.work(0.01)
        self.router.tick(0.01)

    def test_route_to_brain(self):
        client = self._connect()

        msg = {"command": "nop",
               "to": {"user": "niege",
                      "channel": "brain"}}
        self._feed(client, msg)

        self.assertEqual(self.fb.messages, [msg])

    def test_discard_if_not_to_brain(self):
        client = self._connect()

        msg = {"command": "nop",
               "to": {"user": "user",
                      "channel": "channel"}}
        self._feed(client, msg)

        self.assertEqual(self.fb.messages, [])

    def test_switch_user(self):
        client = self._connect()

        msg = {"message": "test",
               "from": {"user": "user",
                        "channel": "channel"},
               "to": {"user": "niege",
                      "channel": "brain"}}
        self._feed(client, msg)

        self.assertEqual(self.fb.messages,
                         [{"command": "switch-user",
                           "user": "user"},
                          msg])

    def test_keep_same_user(self):
        client = self._connect()

        msg = {"message": "test",
               "from": {"user": "user",
                        "channel": "channel"},
               "to": {"user": "niege",
                      "channel": "brain"}}
        self._feed(client, msg)
        self._feed(client, msg)

        self.assertEqual(self.fb.messages,
                         [{"command": "switch-user",
                           "user": "user"},
                          msg, msg])

    def test_route_from_brain(self):
        client1 = self._connect("channel1")
        client2 = self._connect("channel2")
        poll = select.poll()
        poll.register(client1, select.POLLIN)
        poll.register(client2, select.POLLIN)

        self.fb.send_message_to("hello", "user", "channel1:abcd")
        self.router.tick(0.01)

        res = poll.poll(0.01)
        self.assertEqual(res, [(client1.fileno(), select.POLLIN)])
        data = client1.recv(1024)
        msg = json.loads(data.decode())
        self.assertEqual(msg, {"message": "hello",
                               "from": {"user": "niege",
                                        "channel": "brain"},
                               "to": {"user": "user",
                                      "channel": "channel1:abcd"}})

    def test_client_disconnect(self):
        client = self._connect()
        client.close()

        self.fb.send_message_to("hello", "user", "channel:abcd")
        self.router.tick(0.01)

        self.assertEqual(self.fb.messages, [])

    def test_client_gone(self):
        client = self._connect()
        msg = {"message": "test",
               "from": {"user": "user",
                        "channel": "channel"},
               "to": {"user": "niege",
                      "channel": "brain"}}
        self._feed(client, msg)
        self.assertEqual(self.fb.messages.pop(0),
                         {"command": "switch-user",
                          "user": "user"})
        self.assertEqual(self.fb.messages.pop(0), msg)
        self.assertEqual(self.fb.messages, [])

        client.close()
        self.router.tick(0.01)
        self.fb.work(0.01)

        self.assertEqual(self.fb.messages,
                         [{"event": "gone",
                           "from": {"user": "user",
                                    "channel": "channel"},
                           "to": {"user": "niege",
                                  "channel": "brain"}}])
