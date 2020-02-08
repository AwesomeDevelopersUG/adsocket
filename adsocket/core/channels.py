import asyncio
import weakref
import logging

from adsocket.core.exceptions import InvalidChannelException, \
    ChannelNotFoundException, PermissionDeniedException
from .message import Message
from .permissions import DummyPermission
from .signals import new_broker_message
from .utils import import_module
from adsocket.ws.client import Client

_logger = logging.getLogger(__name__)


class Channel:
    """
    Represent single client or multiple client group.
    Before client can join the group all permissions are being check.
    """
    _clients = None

    permissions = []
    _channel_id = None
    _channel_type = None

    def __init__(self, channel_type, channel_id=None):
        self._clients = weakref.WeakSet()
        if channel_id:
            self._channel_id = channel_id
        self._channel_type = channel_type

    def get_permissions(self, client=None):
        permissions = []
        for permission in self.permissions:
            permissions.append(permission())
        return permissions

    async def _check_permissions(self, client, message) -> bool:
        permissions = self.get_permissions(client)

        for permission in permissions:
            result = await permission.can_join(self, client, message)
            if not result:
                return False
        return True

    async def publish(self, msg: Message):
        return await asyncio.gather(
            [client.message(msg) for client in self.clients])

    async def join(self, client: Client, message: Message) -> None:
        access = await self._check_permissions(client, message)
        if not access:
            msg = "You don't have enough permission to join this channel"
            raise PermissionDeniedException(msg)
        self._clients.add(client)

    async def leave(self, client):
        if client in self._clients:
            self._clients.remove(client)

    @property
    def channel_id(self):
        return self._channel_id

    @property
    def type(self):
        return self._channel_type

    @property
    def uid(self):
        return f"{self._channel_type}:{self._channel_id}"

    @property
    def clients(self):
        return self._clients

    def has_client(self, client):
        return client in self.clients

    def is_empty(self):
        return not bool(len(self.clients))

    def __str__(self):
        return f"{self.type}:{self.channel_id}"


class AdminChannel(Channel):

    permissions = [DummyPermission]
    channel_id = "_secret_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        new_broker_message.connect(self._receive_broker_new_message)

    async def _receive_broker_new_message(self, sender, **kwargs):
        await self.publish(kwargs['message'])


class ChannelPool:

    _channels = None
    _types = {}

    def __init__(self, *args, **kwargs):
        self._types = kwargs.pop('channel_types', {})
        permanent_channels = kwargs.pop('permanent_channels', {})
        self._channels = {}
        self._permanent_channels = {}
        self._app = kwargs.get('app', None)

        if len(permanent_channels):
            for name, ch in permanent_channels.items():
                self._create_permanent(name, ch)
        self._app.loop.create_task(self._report())

    def has_type(self, channel):
        """
        Check whether channel type is registered

        :param channel:
        :return:
        """
        return channel in self._types

    def _create_permanent(self, name, ch):
        channel_id = getattr(ch, 'channel_id', None)
        if not channel_id:
            raise Exception("TODO: change to InitializeException")
        uid = f"{name}:{channel_id}"
        self._permanent_channels[uid] = ch
        self._types[name] = ch.__class__
        _logger.info(f"Permanent channel {uid} initialized")

    def _initialize_channel(self, channel_type, channel_id):
        """
        Initialize new instance of channel type with given ID

        :param str channel_type:
        :param str channel_id:
        :return:
        """
        channel_klazz = self._types[channel_type]
        channel_instance = channel_klazz(channel_type, channel_id)
        uid = f"{channel_type}:{channel_id}"
        self._channels[uid] = channel_instance
        _logger.info(f"New channel {uid} initialized")
        return channel_instance

    async def _report(self):
        while True:
            a = len(self._channels)
            b = len(self._permanent_channels)
            msg = f"Channel pool size: {a} | Permanent channel pool size: {b}"
            _logger.info(msg)
            await asyncio.sleep(10)

    def _get_type_and_id(self, channel):
        """
        :param channel:
        :return:
        """
        parts = channel.split(":")
        if len(parts) != 2:
            msg = f"Invalid formatted channel channel_id {channel}. " \
                  f"Try this format 'NAME:ID'"
            raise InvalidChannelException(msg)
        return parts[0], parts[1]

    async def client_disconnected(self, client: Client):
        _logger.debug(f"{client} removed. Let's cleanup channels if possible")
        for name, channel in self._channels.items():
            if channel.has_client(client):
                asyncio.ensure_future(self._schedule_removal(channel))

    async def join_channel(self, channel, client: Client, message: Message):
        _logger.info(f"Client {client} joining channel {channel}")
        channel_type, channel_id = self._get_type_and_id(channel)
        if not self.has_type(channel_type):
            raise InvalidChannelException("Invalid channel type")

        if self.has_channel(channel_type, channel_id):
            channel = self._get_channel(channel_type, channel_id)
        else:
            channel = self._initialize_channel(channel_type, channel_id)

        await channel.join(client, message)
        _logger.info(f"Client {client} has successfully joined {channel}")
        await client.channel_joined(channel)
        return True

    def has_channel(self, channel_type, channel_id):
        """
        Return True if channel exists in the pool otherwise False

        :param str channel_type:
        :param str channel_id:
        :return:
        """
        return f"{channel_type}:{channel_id}" in self._channels

    def _get_channel(self, channel_type, channel_id):
        uid = f"{channel_type}:{channel_id}"
        try:
            return self._channels[uid]
        except KeyError:
            try:
                return self._permanent_channels[uid]
            except KeyError:
                pass
            raise ChannelNotFoundException(f"Channel {uid} was not found")

    def leave_channel(self, channel, client: Client):
        pass

    async def leave_channels(self, client: Client):
        for channel in self._channels:
            if channel.has_client(client):
                await channel.leave(client)
                if len(channel.clients) == 0:
                    asyncio.ensure_future(self._schedule_removal(channel))

    async def _schedule_removal(self, channel: Channel):
        await asyncio.sleep(12)
        if channel.is_empty():
            await self.remove_channel(channel)

    async def remove_channel(self, channel: Channel):
        if channel.uid in self._channels:
            del self._channels[channel.uid]

            _logger.info(f"Channel {channel} have been removed")
            return

    async def publish(self, message):
        """
        This how messages are being ventilated from broker to channel

        :param Message message: message instance
        :return void:
        """
        channel = message.channel
        channel_type, channel_id = self._get_type_and_id(channel)
        if not self.has_type(channel_type):
            raise InvalidChannelException("Invalid channel type")
        channel = self._get_channel(channel_type, channel_id)
        await channel.publish(message)


async def initialize_channels(app):
    """
    Initialize channels by type. Import class from
    klazz string given in settings

    :param app:
    :return:
    """
    if not hasattr(app['settings'], 'CHANNELS') or not \
            isinstance(app['settings'].CHANNELS, dict):
        raise RuntimeError("Improperly configured")

    if not len(app['settings'].CHANNELS):
        _logger.warning("Without channels there is not much to do :(")
    types = {}
    permanent_channels = {}
    for name, options in app['settings'].CHANNELS.items():
        driver = options.pop('driver', None)
        if not driver:
            raise RuntimeError(f'Driver option is missing for channel {name}')
        klazz = import_module(driver)
        create_on_startup = options.pop('create_on_startup', False)
        if create_on_startup:
            options['channel_type'] = name
            permanent_channels[name] = klazz(**options)
        else:
            types[name] = klazz

    app['channels'] = ChannelPool(channel_types=types,
                                  permanent_channels=permanent_channels,
                                  app=app)
