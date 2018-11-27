#!/usr/bin/env python3
import argparse
import atexit
import os
import select
import signal

from tempfile import gettempdir

from runner import Runner

import local


def _term(*_):
    exit()


def main(config_file_name):
    runner = Runner()

    sockname = os.path.join(gettempdir(),
                            "router_{}_socket".format(os.getpid()))
    runner.add("router", "./router.py",
               type="socket", socket=sockname)
    runner.ensure_running("router",
                          with_args=["--socket", sockname,
                                     "--config", config_file_name])
    atexit.register(runner.terminate, "router")

    local.main(sockname)


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, _term)

    parser = argparse.ArgumentParser(description="pa-local",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    main(args.config)
