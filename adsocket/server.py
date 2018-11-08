import logging
import os
from aiohttp import web

from adsocket.core import application, loop
from adsocket.version import __version__
from adsocket.core.utils import import_module

_logger = logging.getLogger('adsocket')


def run_loop():
    """
    Runs the main asyncio event loop. This will run forever till interrupted
    """
    hello_msg = "ADSocket {}".format(__version__)

    _logger.info(hello_msg)

    if os.getenv('ADSOCKET_APPLICATION', None):
        factory = import_module(os.getenv('ADSOCKET_APPLICATION', None))
        app = factory(loop)
        if not isinstance(app, web.Application):
            msg = f"Application must be instance of aiohttp.web.Application " \
                  "but {app.__class__} given"
            raise RuntimeError(msg)
    else:
        app = application.factory(loop)
    if not app:
        _logger.info("Shutdown")
        return
    port = app['settings'].PORT
    host = '0.0.0.0'
    _logger.info(f"Listening on {host}:{port}")
    web.run_app(app, host=host, port=port)


if __name__ == '__main__':
    run_loop()
