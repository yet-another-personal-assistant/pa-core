import socket
import unittest

from runner.channel import EndpointClosedException
from runner.testing import TestChannel

from core.poller import Poller
from utils import timeout


class PollerTest(unittest.TestCase):

    def setUp(self):
        self._poller = Poller()

    def tearDown(self):
        self._poller.close_all()

    def test_blocking_poll(self):
        with self.assertRaisesRegex(Exception, "timeout"):
            with timeout(0.2):
                self._poller.poll()

    def test_timed_poll(self):
        with timeout(0.2):
            result = self._poller.poll(0.1)
        self.assertEqual(list(result), [])

    def test_timed_out_poll(self):
        with self.assertRaisesRegex(Exception, "timeout"):
            with timeout(0.2):
                self._poller.poll(0.3)

    def test_poll_data(self):
        chan = TestChannel()
        self._poller.register(chan)
        chan.put(b'hello\n')

        with timeout(0.2):
            result = self._poller.poll()

        self.assertEqual(list(result), [(b'hello\n', chan)])

    def test_poll_no_data(self):
        chan = TestChannel()
        self._poller.register(chan)

        with timeout(0.2):
            result = self._poller.poll(0.1)

        self.assertEqual(list(result), [])

    def test_poll_accept(self):
        serv = socket.socket()
        serv.bind(('127.0.0.1', 0))
        serv.listen()
        self.addCleanup(serv.close)
        addr, port = serv.getsockname()

        self._poller.add_server(serv)

        client = socket.create_connection((addr, port))
        result = self._poller.poll(0.1)
        self.assertEqual(list(result), [])

        client.send(b'hello\n')

        result = self._poller.poll(0.1)
        self.assertEqual(len(list(result)), 1)

    def test_close_all_channels(self):
        chan = TestChannel()
        self._poller.register(chan)

        self._poller.close_all()

        with self.assertRaises(EndpointClosedException):
            chan.read()

    def test_close_all_servers(self):
        serv = socket.socket()
        serv.bind(('127.0.0.1', 0))
        serv.listen()
        self._poller.add_server(serv)

        self._poller.close_all()

        with timeout(1):
            with self.assertRaises(OSError):
                serv.accept()

    def test_unregister(self):
        chan = TestChannel()
        self._poller.register(chan)
        chan.put(b'hello\n')

        self._poller.unregister(chan)

        with self.assertRaisesRegex(Exception, "timeout"):
            with timeout(0.2):
                self._poller.poll()
