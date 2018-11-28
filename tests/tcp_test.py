import json
import socket
import unittest

from channels.testing import TestChannel

from core.endpoints import TcpEndpoint
from core.routing import RouterDisconnectedException
from utils import timeout


class TcpTest(unittest.TestCase):

    def setUp(self):
        self.serv = socket.socket()
        self.serv.bind(('0.0.0.0', 0))
        self.serv.listen(0)
        self.addr = self.serv.getsockname()
        self.router = TestChannel()
        self.endpoint = TcpEndpoint(self.serv, self.router)

    def tearDown(self):
        self.endpoint.shutdown()
        self.serv.close()
        self.router.close()

    def test_send_name(self):
        self.endpoint.send_name()

        self.assertEqual(self.router.get(), b'tcp\n')

    def _connect(self, username):
        client = socket.create_connection(self.addr)
        client.setblocking(False)
        self.addCleanup(client.close)
        self.endpoint.poll(0.01)
        data = client.recv(1024)
        client.send(username.encode()+b'\n')
        self.endpoint.poll(0.01)
        self.router.get()
        cl_addr = client.getsockname()
        channel = ':'.join(("tcp", cl_addr[0], str(cl_addr[1])))
        return client, channel

    def test_connect(self):
        client = socket.create_connection(self.addr)
        self.addCleanup(client.close)

        self.endpoint.poll(0.01)

        data = client.recv(1024)
        self.assertEqual(data, b'Please enter your name> ')

    #TODO: finish this test
    @unittest.skip
    def test_shutdown(self):
        client = socket.create_connection(self.addr)
        self.addCleanup(client.close)

        self.endpoint.poll(0.01)

        self.endpoint.shutdown()

        # should be an exception, but I don't know which one ... yet
        client.send(b"test\n")

    def test_presence(self):
        client = self._connect("user")
        client = socket.create_connection(self.addr)
        cl_addr = client.getsockname()
        self.addCleanup(client.close)
        self.endpoint.poll(0.01)

        client.send(b'user\n')

        with timeout(0.2):
            self.endpoint.poll(0.01)

        channel = ':'.join(("tcp", cl_addr[0], str(cl_addr[1])))
        data = self.router.get()
        self.assertTrue(data.endswith(b'\n'))
        self.assertEqual(json.loads(data.decode().strip()),
                         {'event': "presence",
                          'from': {'user': "user",
                                   'channel': channel},
                          'to': {'user': 'niege',
                                 'channel': 'brain'}})


    def test_send_hello(self):
        client, channel = self._connect("user")
        client.send(b"hello\n")

        self.endpoint.poll(0.2)

        data = self.router.get()
        self.assertTrue(data.endswith(b'\n'))
        self.assertEqual(json.loads(data.decode().strip()),
                         {'message': "hello",
                          'from': {'user': "user",
                                   'channel': channel},
                          'to': {'user': 'niege',
                                 'channel': 'brain'}})

    def test_show_go_to_bed(self):
        client, channel = self._connect("user")
        self.router.put(json.dumps({'message': 'go to bed',
                                    'to': {'user': "user",
                                           'channel': channel},
                                    'from': {'user': 'niege',
                                             'channel': 'brain'}}).encode())
        self.router.put(b'\n')
        with timeout(0.2):
            self.endpoint.poll(0.01)

        data = client.recv(1024)
        self.assertEqual(data, b'Niege> go to bed\n')

    def test_gone(self):
        client, channel = self._connect("user")

        client.close()

        self.endpoint.poll(0.01)

        data = self.router.get()
        self.assertTrue(data.endswith(b'\n'))
        self.assertEqual(json.loads(data.decode().strip()),
                         {'event': "gone",
                          'from': {'user': "user",
                                   'channel': channel},
                          'to': {'user': 'niege',
                                 'channel': 'brain'}})

    def test_ignore_empty_lines(self):
        client, _ = self._connect("user")
        client.send(b' \n')

        self.endpoint.poll(0.01)

        data = self.router.get()
        self.assertEqual(data, b'')

    def test_router_disconnected(self):
        self.router.close()

        with self.assertRaises(RouterDisconnectedException):
            self.endpoint.poll(0.01)
