import logging

from router.routing import Faucet, Sink, Rule

_LOGGER = logging.getLogger(__name__)


class TgFaucet(Faucet):

    def __init__(self, base_faucet):
        super().__init__()
        self._base = base_faucet

    def read(self):
        event = self._base.read()
        if event and 'message' in event:
            message = event['message']
            if 'chat' in message and message['chat'].get('type') == "private":
                message['from']['media'] = 'telegram'
                return message


class TgSink(Sink):

    def __init__(self, base_sink):
        super().__init__()
        self._base = base_sink

    def write(self, message):
        if 'chat_id' in message:
            if isinstance(message['text'], list):
                msg = message.copy()
                for t in message['text']:
                    msg['text'] = t
                    self._base.write(msg)
            else:
                self._base.write(message)
        else:
            _LOGGER.warning("No chat_id set for message [%s]", message['text'])


class TelegramToBrainRule(Rule):

    def __init__(self, tg_users):
        super().__init__(target="brain", media="telegram")
        self._len += 1
        self._tg_users = tg_users.copy()

    def target_for(self, message):
        source = message['from']
        if source.get('media') == "telegram" and "id" in source:
            return self._tg_users.get(source['id'])
