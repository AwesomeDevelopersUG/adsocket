import logging
from abc import ABC, abstractmethod
import asyncio
from adsocket.core.utils import import_module
from adsocket.core.message import Message
from adsocket.core.exceptions import InvalidChannelException, ChannelNotFoundException

_logger = logging.getLogger(__name__)


class Broker(ABC):

    _app = None

    async def ventilate(self, message: Message):
        try:
            await self.app['channels'].publish(message)
        except InvalidChannelException as e:
            msg = f"Received invalid channel type from Broker: " \
                  f"{message.channel}"
            _logger.error(msg)
        except ChannelNotFoundException:
            pass

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def write(self, msg: Message):
        pass

    @abstractmethod
    async def close(self, app):
        pass


async def load_broker(app):

    params = app['settings'].BROKER

    driver = params.pop('driver')
    broker_class = import_module(driver)
    params['loop'] = app['loop']
    params['app'] = app
    broker = broker_class(**params)
    # await broker.read()
    app['broker'] = broker
    app.loop.create_task(app['broker'].read())
    return app

