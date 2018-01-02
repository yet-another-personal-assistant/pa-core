import logging
from urllib3.exceptions import ProtocolError

from telepot import Bot
from telepot.exception import TelepotException

from router.routing import Faucet, Sink, Rule

_LOGGER = logging.getLogger(__name__)


def init_tg(token):
    return Bot(token)


class TgFaucet(Faucet):

    def __init__(self, bot):
        super().__init__()
        self._bot = bot
        self._messages = []
        self._offset = None

    def read(self):
        if not self._messages:
            updates = []
            try:
                updates = self._bot.getUpdates(offset=self._offset, timeout=0)
            except TelepotException:
                _LOGGER.error("Telegram error", exc_info=True)
            except ProtocolError:
                _LOGGER.error("Urllib error", exc_info=True)
            self._messages.extend(updates)
        if self._messages:
            message = self._messages.pop(0)
            self._offset = message['update_id']+1
            _LOGGER.debug("got message %s", message)
            message = message['message']
            if 'chat' in message and message['chat'].get('type') == "private":
                message['from']['media'] = 'telegram'
                _LOGGER.debug("returning message %s", message)
                return message

    def close(self):
        pass


class TgSink(Sink):

    def __init__(self, bot):
        super().__init__()
        self._bot = bot

    def write(self, message):
        if 'chat_id' in message:
            if isinstance(message['text'], list):
                for line in message['text']:
                    self._bot.sendMessage(message['chat_id'], line)
            else:
                self._bot.sendMessage(message['chat_id'], message['text'])
        else:
            _LOGGER.warning("No chat_id set for message [%s]", message['text'])

    def close(self):
        pass


class TelegramToBrainRule(Rule):

    def __init__(self, tg_users):
        super().__init__(target="brain", media="telegram")
        self._len += 1
        self._tg_users = tg_users.copy()

    def target_for(self, message):
        source = message['from']
        if source.get('media') == "telegram" and "id" in source:
            return self._tg_users.get(source['id'])
