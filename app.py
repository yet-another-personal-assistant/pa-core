#!/usr/bin/env python3
import argparse
import atexit
import signal
import time

from core import Config, Kapellmeister


def _term(*_):
    exit()


def main(config_file_name):
    with open(config_file_name) as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()

    while True:
        time.sleep(3600)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)

    parser = argparse.ArgumentParser(description="pa-main",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", default="config_new.yml")
    args = parser.parse_args()

    main(args.config)
