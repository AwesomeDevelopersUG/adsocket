import asyncio
import weakref
import logging

from adsocket.core.exceptions import InvalidChannelException, \
    ChannelNotFoundException, PermissionDeniedException
from adsocket.core.message import Message
from adsocket.core.permissions import DummyPermission, UserChannelPermission, \
    CompanyChannelPermission
from adsocket.core.signals import new_broker_message
from ..core.utils import import_module
from .client import Client

_logger = logging.getLogger(__name__)


class Channel:
    """
    Represent single client or multiple client group.
    Before client can join the group all permissions are being check.
    """
    _clients = None

    permissions = []
    channel_id = None

    def __init__(self, channel_id=None):
        self._clients = []
        if channel_id:
            self.channel_id = channel_id

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
        for client in self._clients:
            try:
                await client.message(msg)
            except Exception as e:
                _logger.error(f"Couldn't send message {msg} to client {client}")

    async def join(self, client: Client, message: Message) -> None:
        access = await self._check_permissions(client, message)
        if not access:
            msg = "You don't have enough permission to join this channel"
            raise PermissionDeniedException(msg)
        self._clients.append(client)

    async def disconnect(self, client):
        pass

    async def receive(self):
        pass

    @property
    def clients(self):
        return self._clients

    def __str__(self):
        return f"{self.__class__.__name__}:{self.channel_id}"


class AdminChannel(Channel):

    permissions = [DummyPermission]
    channel_id = "_secret_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        new_broker_message.connect(self._receive_broker_new_message)

    async def _receive_broker_new_message(self, sender, **kwargs):
        await self.publish(kwargs['message'])


class UserChannel(Channel):

    permissions = [UserChannelPermission]


class CompanyChannel(Channel):

    permissions = [CompanyChannelPermission]


class GlobalChannel(Channel):
    permissions = [DummyPermission]
    channel_id = "global"


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
        Initialize new instance of channel type and ID

        :param str channel_type:
        :param str channel_id:
        :return:
        """
        channel_klazz = self._types[channel_type]
        channel_instance = channel_klazz(channel_id)
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
            await asyncio.sleep(30)

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
    Initialize channels by type. Import class from klazz string given in settings

    :param app:
    :return:
    """
    if not app['settings'].CHANNELS:
        raise RuntimeError("Improperly configured")
    types = {}
    permanent_channels = {}
    for name, options in app['settings'].CHANNELS.items():
        driver = options.pop('driver', None)
        if not driver:
            raise RuntimeError(f'Driver option is missing for channel {name}')
        klazz = import_module(driver)
        create_on_startup = options.pop('create_on_startup', False)
        if create_on_startup:
            permanent_channels[name] = klazz(**options)
        else:
            types[name] = klazz

    if len(types) == 0 or len(permanent_channels) == 0:
        raise RuntimeError("Sorry.. I cannot work without channels")

    app['channels'] = ChannelPool(channel_types=types,
                                  permanent_channels=permanent_channels,
                                  app=app)
