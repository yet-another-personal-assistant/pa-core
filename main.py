#!/usr/bin/env python3

import logging
import sys


_LOGGER = logging.getLogger(__name__)


def main():
    while True:
        print("> ", end='', flush=True)
        s = sys.stdin.readline()
        print("Niege> Ой, приветик!")


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    main()
