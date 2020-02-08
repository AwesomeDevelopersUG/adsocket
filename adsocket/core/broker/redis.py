import asyncio
import json
import logging

from aioredis.pubsub import Receiver
import aioredis

from adsocket.core.signals import new_broker_message
from . import Broker
from adsocket.core.message import Message

_logger = logging.getLogger(__name__)


class RedisBroker(Broker):

    _redis = None
    _db = None
    _subscribe = None
    loop = None
    _channels = None
    app = None

    def __init__(self, host, db, loop, app, channels):
        self._host = host
        self._db = db
        self.loop = loop
        self.app = app
        self._channels = channels

    @property
    async def redis(self):
        if not self._redis:
            _logger.info(f"Connecting to redis {self._host} - DB: {self._db}")

            redis = await aioredis.create_redis(self._host)
            await redis.select(self._db)
            self._redis = redis
            _logger.info("Connection to redis seems to be solid")
        return self._redis

    @property
    async def subscribe(self):
        if not self._subscribe:
            redis = await self.redis
            # self._subscribe = await redis.subscribe('ws')
            r = Receiver(loop=self.loop)
            for ch in self._channels:
                await redis.subscribe(r.channel(ch))
            self._subscribe = r
        return self._subscribe

    async def read(self):
        _logger.info("Waiting for messages")
        sub = await self.subscribe
        async for channel, msg in sub.iter():
            _logger.info("New message")
            msg = json.loads(msg)
            msg = Message.from_json(msg)
            await self.ventilate(msg)
            self.app.loop.create_task(new_broker_message.send(message=msg))
            # asyncio.ensure_future(new_broker_message.send(message=msg))
        _logger.info("No longer receiving messages from redis")

    async def get_authentication_credentials(self, key):
        redis = await self.redis
        return redis.get(key)

    async def write(self, message):
        pass

    async def close(self, app):
        redis = await self.redis
        redis.close()
        await redis.wait_closed()
