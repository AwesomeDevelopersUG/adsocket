import logging
import os
from logging import config
from raven.transport.base import AsyncTransport
from raven.transport.http import HTTPTransport

from adsocket.core import loop
from concurrent.futures import ThreadPoolExecutor


_default_level = logging.DEBUG if bool(os.getenv('ZEENR_DEBUG_LOGGING', False)) else logging.INFO  # noqa

logging.basicConfig(
    level=_default_level,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)


def setup_logging(settings):
    """
    Reconfigure logging from settings. This will override the default logging
    configuration completely.

    :param dict settings: The `logging` settings dictionary
    """
    # logging.config.dictConfig(settings)


class SentryTransport(AsyncTransport, HTTPTransport):
    """
    Sentry custom Transport avoiding blocking request to sentry by sending
    request through scheduling executor
    """

    def async_send(self, data, headers, success_cb, failure_cb):
        """
        When application starts there is small windows when executor is not
        initialized yet, so we need to start it without telemetry.
        Executor will be re-initialized afterwards

        :param dict data: log data
        :param dict headers: custom request headers
        :param function success_cb: success callback
        :param function failure_cb: failure callback
        :return:
        """

        # if not scheduling.executor._executor:
        #     from zeenr_microsite.conf import app_settings
        #     scheduling.executor.init(None, app_settings.EXECUTOR_POOL_SIZE)
        scheduling = ThreadPoolExecutor()
        loop.run_in_executor(scheduling,
                             super().send, data, headers)
