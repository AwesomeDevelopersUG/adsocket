import abc
import logging

from adsocket.core.exceptions import InvalidChannelException, \
    PermissionDeniedException
from adsocket.core.message import Message
from adsocket.core.utils import parse_channel
from adsocket.ws import Client


_logger = logging.getLogger(__name__)


class AbstractCommand(abc.ABC):

    _app = None

    def __init__(self, app):
        self._app = app

    async def execute(self, client: Client, message: Message):
        """

        :param client.Client client: Client instance
        :param core.Message message: Message instance
        :return void:
        """


class PublishCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        pass


class SubscribeCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        """
        Subscribe client to channel(s)

        :param client:
        :param core.Message message: Message instance
        :return bool void:
        """
        chpool = self._app['channels']

        channels = message.channel
        if channels and not isinstance(channels, list):
            channels = [channels]

        if not channels:
            raise InvalidChannelException("Invalid channel format")

        results = {}
        for channel in channels:
            orig_channel = channel
            channel = parse_channel(channel)
            channel_type, channel_id = channel
            if not chpool.has_type(channel_type):
                results[orig_channel] = "Channel not found"
                break
                # raise ChannelNotFoundException("Channel type not found")
            try:
                result = await chpool.join_channel(orig_channel, client,
                                                   message)
            except PermissionDeniedException:
                results[orig_channel] = "Permission denied"
            except Exception as e:
                _logger.exception(e)
                results[orig_channel] = "Internal server error"
            else:
                results[orig_channel] = result

        if message.can_respond():
            response = {'result': results}
            message.set_response(response)
            return await client.message(message)


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


class PingCommand(AbstractCommand):

    async def execute(self, client: Client, message: Message):
        if message.can_respond():
            message.set_response('pong')
            await client.message(message)