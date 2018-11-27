import json
import logging

from channels import EndpointClosedException
from channels.poller import Poller


_LOGGER = logging.getLogger(__name__)


class Router:

    def __init__(self, serv, be):
        self._serv = serv
        self._be = be
        self._poller = Poller(buffering='line')
        self._poller.add_server(self._serv)
        self._poller.register(self._be)
        self._current_user = None
        self._endpoints = {}
        self._endpoint_names = {}
        self._endpoint_users = {}

    def _get_endpoint(self, endpoint_name):
        return self._endpoints.get(endpoint_name.split(':', 1)[0])

    def _add_endpoint(self, endpoint, name):
        _LOGGER.debug("Registered endpoint %s", name)
        self._endpoint_names[endpoint] = name
        self._endpoints[name] = endpoint
        self._endpoint_users[endpoint] = set()

    def _remove_endpoint(self, endpoint):
        name = self._endpoint_names.get(endpoint)
        if name is not None:
            _LOGGER.debug("Removing endpoint %s", name)
            del self._endpoint_names[endpoint]
            del self._endpoints[name]
            gone_msg = {"event": "gone",
                        "from": {"channel": name},
                        "to": {"user": "niege",
                               "channel": "brain"}}
            for user in self._endpoint_users[endpoint]:
                self._switch_user(user)
                gone_msg["from"]["user"] = user
                self._be.write(json.dumps(gone_msg).encode()+b'\n')
            del self._endpoint_users[endpoint]
        endpoint.close()

    def _switch_user(self, user):
        if user != self._current_user:
            switch_msg = {"command": "switch-user",
                            "user": user}
            self._be.write(json.dumps(switch_msg).encode(), b'\n')
            self._current_user = user

    def _route_user_message(self, channel, data):
        if channel not in self._endpoint_names:
            name = data.decode().strip()
            self._add_endpoint(channel, name)
            return
        msg = json.loads(data.decode())
        if msg['to']['channel'] != 'brain':
            return
        if 'from' in msg:
            user = msg["from"]["user"]
            self._switch_user(user)
            self._endpoint_users[channel].add(user)
        self._be.write(data)

    def tick(self, timeout=None):
        for data, channel in self._poller.poll(timeout):
            _LOGGER.debug("Got %s on %s", data, channel)
            if channel == self._serv:
                continue
            elif channel == self._be:
                msg = json.loads(data.decode())
                endpoint = self._get_endpoint(msg['to']['channel'])
                if endpoint is not None:
                    try:
                        endpoint.write(data)
                    except EndpointClosedException:
                        self._remove_endpoint(channel)
            else:
                if data:
                    self._route_user_message(channel, data)
                else:
                    self._remove_endpoint(channel)
