import os
import shutil
import time
import unittest

from tempfile import mkdtemp

from runner.channel import EndpointClosedException

from core import Config, Kapellmeister
from utils import timeout


class KapellmeisterTest(unittest.TestCase):

    def test_no_components(self):
        km = Kapellmeister(Config("components:\n"))

        km.run()

    def test_one_component(self):
        cfg = '''
            components:
              echo:
                command: echo hello, world
        '''
        km = Kapellmeister(Config(cfg))
        km.run()

        channel = km.connect("echo")

        with timeout(1):
            line = b''
            while not line.endswith(b'\n'):
                line += channel.read()
        self.assertEqual(line, b'hello, world\n')

    def test_two_components(self):
        dirname = mkdtemp()
        sock = os.path.join(dirname, "sock")
        self.addCleanup(shutil.rmtree, dirname)
        cfg = '''
            components:
              socat1:
                command: socat STDIO UNIX-LISTEN:{sock}
              socat2:
                command: socat UNIX:{sock} STDIO
                after: socat1
        '''.format(sock=sock)
        km = Kapellmeister(Config(cfg))
        km.run()

        channel1 = km.connect("socat1")
        channel2 = km.connect("socat2")

        channel1.write(b'howdy\n')

        with timeout(1):
            line = b''
            while not line.endswith(b'\n'):
                line += channel2.read()
        self.assertEqual(line, b'howdy\n')

    def test_tmpname(self):
        cfg = '''
            variables:
              FILE: tmpfile
            components:
              touch:
                command: touch ${FILE}
        '''
        km = Kapellmeister(Config(cfg))
        km.run()

        filename = km.get_variable('FILE')

        self.assertIsNotNone(filename)
        with timeout(0.1):
            while not os.path.exists(filename):
                time.sleep(0.01)

    def test_link_socats(self):
        cfg = '''
            variables:
              SOCK: tmpfile
            components:
              socat1:
                command: socat STDIO UNIX-LISTEN:${SOCK}
              socat2:
                command: socat STDIO UNIX:${SOCK}
                after: socat1
        '''
        km = Kapellmeister(Config(cfg))
        km.run()

        channel1 = km.connect("socat1")
        channel2 = km.connect("socat2")

        channel1.write(b'howdy\n')

        with timeout(1):
            line = b''
            while not line.endswith(b'\n'):
                line += channel2.read()
        self.assertEqual(line, b'howdy\n')

    def test_single_socat(self):
        cfg = '''
            variables:
              SOCK: tmpfile
            components:
              socat:
                command: socat SYSTEM:cat UNIX-LISTEN:${SOCK}
                type: socket
                socket: ${SOCK}
        '''
        km = Kapellmeister(Config(cfg))
        with timeout(1):
            km.run()

        channel = km.connect("socat")

        channel.write(b'howdy\n')

        with timeout(1):
            line = b''
            while not line.endswith(b'\n'):
                line += channel.read()
        self.assertEqual(line, b'howdy\n')

    def test_undef_variables(self):
        config = Config("""
            components:
              component:
                command: touch ${file}
        """)

        km = Kapellmeister(config)

        with self.assertRaises(KeyError):
            km.run()

    def test_terminate(self):
        config = Config("""
            components:
              cat:
                command: cat
        """)

        km = Kapellmeister(config)
        km.run()
        chan = km.connect("cat")

        km.terminate()

        with self.assertRaises(EndpointClosedException):
            chan.read()
