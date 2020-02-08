import logging

from aiohttp.web_ws import WebSocketResponse
from aiohttp import WSCloseCode
import uuid
import asyncio
import weakref

from ..core.exceptions import ClientException
from ..core.message import Message

KICKOUT_CMD = "system.kickout"
_logger = logging.getLogger(__name__)


class Client:

    _ws = None
    _request = None
    _history = []

    _channels = None

    _client_id = None
    _profile = {}
    _authenticated = False

    def __init__(self, ws: WebSocketResponse, client_id=None, profile=None):
        self._ws = weakref.ref(ws)
        self._channels = weakref.WeakSet()
        self._client_id = client_id or uuid.uuid4()
        self._state = {}
        self._profile = profile or {}
        self._authenticated = False

    @property
    def client_id(self):
        return self._client_id

    async def message(self, msg: Message) -> None:
        try:
            return await self.ws.send_str(msg.to_json())
        except Exception as e:
            _logger.exception(e)

    async def set_authenticated(self):
        """
        Mark client as Authenticated
        :return void:
        """
        self._authenticated = True

    async def is_authenticated(self):
        return bool(self._authenticated)

    @property
    def profile(self):
        return self._profile

    @profile.setter
    def profile(self, data):
        self._profile = data

    async def disconnect(self):
        """
        :return:
        :rtype:
        """
        if not self.ws.closed:
            await self.ws.close(code=WSCloseCode)
        # reset websocket reference
        self._ws = None

    @property
    def ws(self):
        return self._ws()

    @property
    def channels(self):
        return self._channels

    def join_channel(self, channel):
        if channel in self._channels:
            return
        self._channels.add(channel)

    async def channel_joined(self, channel):
        self._channels.add(channel)

    def __setitem__(self, key, value):
        self._state[key] = value

    def __getitem__(self, key):
        return self._state[key]

    def __delitem__(self, key):
        del self._state[key]

    def __iter__(self):
        return iter(self._state)

    def __str__(self):
        if self.client_id:
            return f"Client:{self.client_id}"
        return "Client:no-id"


class ClientPool:
    """
    Holds and manage all clients connected to websocket
    """

    def __init__(self, app):
        self._clients = weakref.WeakSet()
        self._app = app
        self._kickout_message = Message(
            type=KICKOUT_CMD,
            data={'reason': "You've not authenticated yourself yet"}
        )
        self._active_count = 0
        self._app.loop.create_task(self._report())

    async def _schedule_for_disconnect(self, client: Client):
        """
        Unauthenticated users should be disconnected after while

        :param client:
        :return:
        """
        await asyncio.sleep(self._app['settings'].DISCONNECT_UNAUTHENTICATED)
        if not await client.is_authenticated():
            await self.kickout(client)

    async def _report(self):
        while True:
            await asyncio.sleep(30)
            _logger.info("Client pool size: {}".format(len(self._clients)))

    def _client_disconnected(self, client: Client):
        asyncio.ensure_future(self._app['channels'].client_disconnected(client))

    async def append(self, client: Client):
        if self.is_client(client):
            raise ClientException(f"Client is already member: {client}")
        self._clients.add(client)
        if self._app['settings'].DISCONNECT_UNAUTHENTICATED:
            asyncio.ensure_future(self._schedule_for_disconnect(client))
        self._active_count += 1
        # This is actually hack.. I don't know why but finalize
        # for client instance doesn't work
        weakref.finalize(client.ws, self._client_disconnected, client)
        return True

    async def remove(self, client: Client):
        """
        Remove client from pool

        :param client:
        :return:
        """

        await client.disconnect()
        self._clients.discard(client)
        self._active_count -= 1

    def is_client(self, client: Client) -> bool:
        """
        Is client member of this pool
        :param client:
        :return:
        """

        return client in self._clients

    async def active_count(self) -> int:
        """
        Return number of action clients
        :return:
        """
        return self._active_count

    async def broadcast(self, message: Message):
        for client in self._clients:
            client.message(message)
        return True

    async def kickout(self, client: Client):
        """
        Kick client out for some reason
        :param client:
        :return:
        """
        await client.message(self._kickout_message)
        asyncio.ensure_future(client.disconnect())

    async def shutdown(self, app):
        """
        Kick all connected

        :param app:
        :return:
        """
        for client in self._clients:
            await client.disconnect()
