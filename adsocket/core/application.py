import asyncio
from aiohttp import web
import aioredis

from adsocket.core.logging_setup import setup_logging
from adsocket.ws import ws_handler, http_handler
from adsocket import conf, banner
from adsocket.core.broker import load_broker
from adsocket.core.auth import initialize_authentication
from adsocket.ws.channels import initialize_channels
from adsocket.ws.client import ClientPool
from adsocket.core.commands import commander


async def _initialize_redis(app):
    settings = app['settings']
    pool = await aioredis.create_pool(
        settings.REDIS_HOST,
        minsize=settings.REDIS_MIN_POOL_SIZE,
        maxsize=settings.REDIS_MAX_POOL_SIZE,
        loop=app['loop'])
    app['redis'] = pool
    return app


async def _on_shutdown(app):
    """

    :param aiohttp.web.Application app: aiohttp Application instance
    :return:
    """
    await app['broker'].close(app)
    await app['client_pool'].shutdown(app)
    app['redis'].close()
    app['redis'].wait_closed()


def factory(loop):

    settings = conf.app_settings

    app = web.Application(
        loop=loop,
        debug=settings.DEBUG,
    )

    # app['settings'] = conf.app_settings
    app['settings'] = settings
    app['loop'] = loop
    app.router.add_get('/ws', ws_handler)
    app.router.add_get('/poll', http_handler)
    setup_logging(app['settings'].LOGGING)
    app['client_pool'] = ClientPool(app)
    asyncio.ensure_future(load_broker(app))
    asyncio.ensure_future(initialize_channels(app))
    asyncio.ensure_future(initialize_authentication(app))
    asyncio.ensure_future(_initialize_redis(app))
    app.on_shutdown.append(_on_shutdown)
    # we also need commander to have control over the commands
    commander.set_app(app)
    app['commander'] = commander

    return app


