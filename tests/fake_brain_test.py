import json
import socket
import unittest

from core.testing import FakeBrain
from utils import timeout


class FakeBrainTest(unittest.TestCase):

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

    def _connect_client(self, user_name):
        sock = socket.create_connection(self._fb.addr)
        self._fb.work(1)

        addr, port = sock.getsockname()
        cl_addr = "tcp:"+addr+":"+str(port)
        
        sock.send(json.dumps({"event": "presence",
                              "from": {"user": "user",
                                       "channel": cl_addr},
                              "to": "brain"}).encode()+b'\n')

        self._fb.work(1)

        return sock, cl_addr


    def test_presence_message(self):
        _, cl_addr = self._connect_client('user')

        self.assertEqual(len(self._fb.users), 1)
        self.assertIn('user', self._fb.users)
        self.assertEqual(len(self._fb.users['user']['channels']), 1)
        self.assertIn(cl_addr, self._fb.users['user']['channels'])

    def test_send_message_to(self):
        sock, cl_addr = self._connect_client('user')

        self._fb.send_message_to("test", user="user", channel=cl_addr)

        with timeout(0.2):
            data = sock.recv(1024)
        self.assertTrue(data.endswith(b'\n'))
        msg = json.loads(data.decode().strip())
        self.assertEqual(msg, {"message": "test",
                               "from": "brain",
                               "to": {"user": "user",
                                      "channel": cl_addr}})

    def test_echo(self):
        sock, cl_addr = self._connect_client('user')

        sock.send(json.dumps({"message": "test",
                              "from": {"user": "user",
                                       "channel": cl_addr},
                              "to": "brain"}).encode()+b'\n')
        self._fb.work(1)

        with timeout(0.2):
            data = sock.recv(1024)
        self.assertTrue(data.endswith(b'\n'))
        msg = json.loads(data.decode().strip())
        self.assertEqual(msg, {"message": "test",
                               "from": "brain",
                               "to": {"user": "user",
                                      "channel": cl_addr}})
