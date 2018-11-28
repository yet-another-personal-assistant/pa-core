import json
import logging

from channels.poller import Poller

from core.routing import RouterDisconnectedException


_LOGGER = logging.getLogger(__name__)


class TcpEndpoint:

    def __init__(self, serv, router_channel):
        self._router = router_channel
        self._serv = serv
        self._clients = {}
        self._client_names = {}
        self._usernames = {}
        self._poller = Poller(buffering='line')
        self._poller.add_server(serv)
        self._poller.register(self._router)

    def send_name(self):
        self._router.write(b'tcp\n')

    def poll(self, timeout=None):
        for data, channel in self._poller.poll(timeout):
            _LOGGER.debug("Got %s from %s", data, channel)
            if channel == self._serv:
                addr, client = data
                client.write(b'Please enter your name> ')
                client_name = 'tcp:'+addr[0]+':'+str(addr[1])
                self._clients[client_name] = client
                self._client_names[client] = client_name
            elif channel == self._router:
                if not data:
                    raise RouterDisconnectedException()
                msg = json.loads(data.decode())
                client = self._clients.get(msg['to']['channel'])
                if client is not None:
                    client.write(b'Niege> '+msg['message'].encode()+b'\n')
            else:
                line = data.decode().strip()
                username = self._usernames.get(channel)
                if username is None:
                    presence_msg = {"event": "presence",
                                    "from": {"user": line,
                                             "channel": self._client_names[channel]},
                                    "to": {"user": "niege",
                                           "channel": "brain"}}
                    self._router.write(json.dumps(presence_msg).encode(), b'\n')
                    self._usernames[channel] = line
                elif data:
                    if line:
                        msg = {"message": line,
                               "from": {"user": username,
                                        "channel": self._client_names[channel]},
                               "to": {"user": "niege",
                                      "channel": "brain"}}
                        self._router.write(json.dumps(msg).encode(), b'\n')
                else:
                    client_name = self._client_names[channel]
                    gone_msg = {"event": "gone",
                                "from": {"user": username,
                                         "channel": client_name},
                                "to": {"user": "niege",
                                       "channel": "brain"}}
                    self._router.write(json.dumps(gone_msg).encode(), b'\n')
                    channel.close()
                    del self._clients[client_name]
                    del self._client_names[channel]
                    del self._usernames[channel]

    def shutdown(self):
        for client in self._client_names:
            client.close()

        self._clients.clear()
        self._client_names.clear()
        self._usernames.clear()
