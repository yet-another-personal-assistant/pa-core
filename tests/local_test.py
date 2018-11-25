import getpass
import json
import socket
import unittest

from channels.testing import TestChannel

import local

class LocalEndpointTest(unittest.TestCase):

    def setUp(self):
        self.stdio = TestChannel()
        self.router = TestChannel()
        local.set_stdio(self.stdio)
        local.set_router(self.router)
        self.channel = 'local:'+socket.gethostname()
        self.user = getpass.getuser()

    def tearDown(self):
        local.set_stdio(None)
        local.set_router(None)
        self.stdio.close()
        self.router.close()

    def test_endpoint_name(self):
        local.send_name()

        self.assertEqual(self.router.get(), b'local\n')

    def test_send_hello(self):
        self.stdio.put(b"hello")

        local.poll(0.2)

        data = self.router.get()
        self.assertTrue(data.endswith(b'\n'))
        self.assertEqual(json.loads(data.decode().strip()),
                         {'message': "hello",
                          'from': {'user': self.user,
                                   'channel': self.channel},
                          'to': {'user': 'niege',
                                 'channel': 'brain'}})

    def test_show_go_to_bed(self):
        self.router.put(json.dumps({'message': 'go to bed',
                                    'to': {'user': self.user,
                                           'channel': self.channel},
                                    'from': {'user': 'niege',
                                             'channel': 'brain'}}).encode())
        self.router.put(b'\n')

        local.poll(0.2)

        data = self.stdio.get()
        self.assertEqual(data, b'Niege> go to bed\n')

    def test_ignore_empty_lines(self):
        self.stdio.put(b" \n")

        local.poll(0.2)

        data = self.router.get()
        self.assertEqual(data, b'')
