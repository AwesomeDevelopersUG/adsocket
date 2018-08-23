import abc

from adsocket.core.exceptions import InvalidChannelException, \
    ChannelNotFoundException
from adsocket.core.message import Message
from adsocket.core.utils import parse_channel
from adsocket.ws import Client


class AbstractCommand(abc.ABC):

    _app = None

    def __init__(self, app):
        self._app = app

    async def execute(self, client: Client, message: Message):
        pass


class PublishCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        pass


class SubscribeCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        """
        Subscribe client to channel(s)

        :param client:
        :param message:
        :return:
        """
        chpool = self._app['channels']
        result = parse_channel(message.channel)
        if not result:
            raise InvalidChannelException("Invalid channel format")
        channel_type, channel_id = result

        if not chpool.has_type(channel_type):
            raise ChannelNotFoundException("Channel type not found")
        result = await chpool.join_channel(message.channel, client, message)
        if result and message.can_respond():
            message.set_response({'result': result})
            await client.message(message)


class UnsubscribeCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        chpool = self._app['channels']
        result = parse_channel(message.channel)
        if not result:
            raise InvalidChannelException("Invalid channel format")
        channel_type, channel_id = result


class AuthenticateCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        """
        This command execute registered authenticators one by one until
        one authenticator succeed

        :param Client client:
        :param Message message:
        :return:
        """
        authenticators = self._app['authenticators']
        for auth in authenticators:
            result, data = await auth.authenticate(client, message)
            if result:
                client.profile = data
                await client.set_authenticated()
                await self._send_response(client, message, True)
                return True, auth
        if message.can_respond():
            await self._send_response(client, message, False)
        return False,

    async def _send_response(self, client, message, result):
        """
        Send result of authentication to client if possible

        :param client:
        :param message:
        :param result:
        :return:
        """
        if message.can_respond():
            message.set_response({'result': result})
            await client.message(message)
