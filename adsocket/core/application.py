import asyncio
from aiohttp import web
import aioredis

from .logging_setup import setup_logging
from adsocket.ws import ws_handler, http_handler
from adsocket.http_handlers import ping_handler
from adsocket import conf, banner
from .broker import load_broker
from .auth import initialize_authentication
from .channels import initialize_channels
from ..ws.client import ClientPool
from .commands import commander


async def _initialize_redis(app):
    """
    This is actually hack. Once I have time I'll move it to somewhere
    else or maybe even delete it

    :param aiohttp.web.Application app: Application instance
    :return aiohttp.web.Application: Application instance
    """
    settings = app['settings']
    pool = await aioredis.create_pool(
        settings.REDIS_HOST,
        db=settings.REDIS_DB,
        minsize=settings.REDIS_MIN_POOL_SIZE,
        maxsize=settings.REDIS_MAX_POOL_SIZE,
        loop=app['loop'])
    app['redis'] = pool


async def _on_shutdown(app):
    """

    :param aiohttp.web.Application app: aiohttp Application instance
    :return:
    """
    await app['broker'].close(app)
    await app['client_pool'].shutdown(app)
    app['redis'].close()
    await app['redis'].wait_closed()


def factory(loop):

    settings = conf.app_settings

    app = web.Application(
        loop=loop,
        debug=settings.DEBUG,
    )

    app['settings'] = settings
    app['loop'] = loop
    # Backward compatibility only
    app.router.add_get('/ws', ws_handler)
    # This is intended
    app.router.add_get('/', ws_handler)
    app.router.add_get('/_ping', ping_handler)
    setup_logging(app['settings'].LOGGING)
    app['client_pool'] = ClientPool(app)
    asyncio.ensure_future(load_broker(app))
    asyncio.ensure_future(initialize_channels(app))
    asyncio.ensure_future(initialize_authentication(app))
    loop.run_until_complete(_initialize_redis(app))
    app.on_shutdown.append(_on_shutdown)
    # we also need commander to have control over the commands
    commander.set_app(app)
    app['commander'] = commander

    return app


