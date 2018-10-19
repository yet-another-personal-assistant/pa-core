import json
import socket

from channels.poller import Poller


class FakeBrain:

    def __init__(self):
        self._serv = socket.socket()
        self._serv.bind(('127.0.0.1', 0))
        self._serv.listen()
        self.addr = self._serv.getsockname()
        self.users = {}
        self._poller = Poller()
        self._poller.add_server(self._serv)

    def work(self, duration):
        for data, channel in self._poller.poll(duration):
            print("Got", data, "from", channel)
            if channel == self._serv:
                addr, client = data
            else:
                msg = json.loads(data.decode().strip())
                if 'message' in msg:
                    channel.write(json.dumps({"message": msg['message'],
                                              "from": msg['to'],
                                              "to": msg['from']}).encode()+b'\n')
                elif 'event' in msg:
                    user = msg['from']['user']
                    u_channel = msg['from']['channel']
                    self.users[user] = {'channels': {u_channel: channel}}

    def send_message_to(self, message, user, channel):
        chan = self.users[user]['channels'][channel]
        chan.write(json.dumps({"message": message,
                               "from": "brain",
                               "to": {'user': user,
                                      'channel': channel}}).encode()+b'\n')

    def shutdown(self):
        self._serv.close()
