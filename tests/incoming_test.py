import json
import os
import shutil
import socket
import stat
import unittest

from tempfile import mkdtemp

from channels.testing import TestChannel

from core.endpoints import IncomingEndpoint
from utils import timeout


class IncomingEndpointTest(unittest.TestCase):

    def setUp(self):
        self.dir = mkdtemp()
        self.router = TestChannel()
        self.addCleanup(shutil.rmtree, self.dir)

        self.pipe = os.path.join(self.dir, "PIPE")
        self.endpoint = IncomingEndpoint(self.pipe, self.router)

    def tearDown(self):
        self.router.close()
        self.endpoint.shutdown()

    def test_create_pipe(self):
        self.assertTrue(os.path.exists(self.pipe))
        self.assertTrue(stat.S_ISFIFO(os.stat(self.pipe).st_mode))

    def test_cleanup_pipe(self):
        self.endpoint.shutdown()
        self.assertFalse(os.path.exists(self.pipe))

    def test_send_name(self):
        self.assertEqual(self.router.get(), b'incoming\n')

    def test_send_data(self):
        self.router.get()
        with timeout(0.2):
            with open(self.pipe, 'wb') as pipe:
                pipe.write(b'hello\n')

        with timeout(0.2):
            self.endpoint.poll(0.01)

        self.assertEqual(self.router.get(), b'hello\n')
