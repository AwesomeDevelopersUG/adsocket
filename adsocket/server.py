import logging
from aiohttp import web

from adsocket.core import application, loop
from adsocket.version import __version__
_logger = logging.getLogger('adsocket')


def run_loop():
    """
    Runs the main asyncio event loop. This will run forever till interrupted
    """
    hello_msg = "Zeenr Websocket {}".format(__version__)

    #
    # _logger.info(art)
    _logger.info(hello_msg)
    # _logger.info(len(hello_msg) * "=")

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
