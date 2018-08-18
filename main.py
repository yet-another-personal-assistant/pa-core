#!/usr/bin/env python3

import logging
import sys
import time

_LOGGER = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    print("> ", end='', flush=True)
    s = sys.stdin.readline()
    print("Niege> Ой, приветик!")
    print("> ", end='', flush=True)
