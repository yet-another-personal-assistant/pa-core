import json
import logging
import socket

from channels.poller import Poller


_LOGGER = logging.getLogger(__name__)

class FakeBrain:

    def __init__(self):
        self._serv = socket.socket()
        self._serv.bind(('127.0.0.1', 0))
        self._serv.listen()
        self.addr = self._serv.getsockname()
        self.messages = []
        self._poller = Poller(buffering='line')
        self._poller.add_server(self._serv)
        self._client = None
        self._active_user = None

    def work(self, duration):
        for data, channel in self._poller.poll(duration):
            _LOGGER.debug("Got %s from %s", data, channel)
            if channel == self._serv:
                _, self._client = data
            else:
                msg = json.loads(data.decode().strip())
                self.messages.append(msg)
                if 'message' in msg and msg['from']['user'] == self._active_user:
                    channel.write(json.dumps({"message": msg['message'],
                                              "from": msg['to'],
                                              "to": msg['from']}).encode()+b'\n')
                elif 'command' in msg:
                    if msg['command'] == 'switch-user':
                        self._active_user = msg['user']

    def send_message_to(self, message, user, channel):
        _LOGGER.debug("Writing message '%s' to user %s channel %s", message, user, channel)
        self._client.write(json.dumps({"message": message,
                                       "from": "brain",
                                       "to": {'user': user,
                                              'channel': channel}}).encode()+b'\n')

    def shutdown(self):
        self._serv.close()
        if self._client is not None:
            self._client.close()
