import time
import unittest

from utils import timeout

class UtilsTest(unittest.TestCase):

    def test_timeout(self):
        with timeout(0.01):
            with self.assertRaises(Exception):
                time.sleep(0.05)

    def test_no_timeout(self):
        with timeout(0.05):
            time.sleep(0.01)
        time.sleep(0.05)
