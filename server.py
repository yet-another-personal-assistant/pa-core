#!/usr/bin/env python3
import argparse
import json
import logging
import socket
import sys

from channels.poller import Poller

from core import Config, Kapellmeister

_LOGGER = logging.getLogger(__name__)


def main(addr, port, config_file_name):
    with open(config_file_name) as cfg:
        config = Config(cfg.read())
    km = Kapellmeister(config)
    km.run()

    poller = Poller(buffering='line')
    brain = km.connect("brain")
    poller.register(brain)

    serv = socket.socket()
    serv.bind((addr, port))
    addr, port = serv.getsockname()
    serv.listen()
    poller.add_server(serv)
    print("Server started on", addr+':'+str(port))
    sys.stdout.flush()

    usernames = {}
    chan2name = {}
    name2chan = {}

    while True:
        for data, channel in poller.poll():
            if channel == serv:
                addr, cl_chan = data
                chan_name = 'tcp:'+addr[0]+':'+str(addr[1])
                chan2name[cl_chan] = chan_name
                name2chan[chan_name] = cl_chan
                _LOGGER.debug("Added channel %s as %s", cl_chan, chan_name)
                cl_chan.write(b'Please enter your name> ')
            elif channel == brain:
                msg = json.loads(data.decode().strip())
                _LOGGER.debug("Message from brain: %s", msg)
                channel_name = msg['to']['channel']
                chan = name2chan[channel_name]
                chan.write(b'Niege> '+msg['message'].encode(), b'\n')
            else:
                _LOGGER.debug("Got data: %s", repr(data))
                line = data.decode().strip()
                if channel not in usernames:
                    _LOGGER.debug("Sending user name \"%s\" for channel %s", line, channel)
                    presence_msg = {'event': 'presence',
                                    'from': {'user': line,
                                             'channel':chan2name[channel]},
                                    'to': 'brain'}
                    brain.write(json.dumps(presence_msg).encode(), b'\n')
                    usernames[channel] = line
                else:
                    _LOGGER.debug("Sending message from channel %s", channel)
                    brain.write(json.dumps({"message": line,
                                            "from": {"user": usernames[channel],
                                                     "channel": chan2name[channel]},
                                            "to": {"user": "niege",
                                                   "channel": "brain"}}).encode(),
                                b'\n')


if __name__ == '__main__':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="pa-server",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--host", help="host to bind to", default='0.0.0.0')
    parser.add_argument("--port", type=int, help="port to use", default=8001)
    parser.add_argument("--config", default="config.yml")
    args = parser.parse_args()

    main(args.host, args.port, args.config)
