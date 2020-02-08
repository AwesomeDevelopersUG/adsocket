import logging
from abc import ABC, abstractmethod
from aioredis import RedisError

from adsocket.core.exceptions import AuthenticationException
from adsocket.core.message import Message
from adsocket.core.utils import import_module

_logger = logging.getLogger(__name__)


class AbstractAuth(ABC):
    """
    Abstract Authenticator must be base subclass for every custom
    authentication class
    """
    _app = None

    def __init__(self, app):
        self._app = app

    @abstractmethod
    async def authenticate(self, client, message):
        """

        :param client:
        :param message:
        :return:
        """


class UsernamePasswordAuth(AbstractAuth):

    credentials = (("admin", "admin"),)

    async def authenticate(self, client, message: Message):
        username = message.data.get('username', None)
        password = message.data.get('password', None)

        for auth in self.credentials:
            result = username == auth[0] and password == auth[1]
            if result is True:
                return result, {}
        return False, None


async def initialize_authentication(app):
    _logger.info("Registering authentication classes")
    if not app['settings'].AUTHENTICATION_CLASSES:
        _logger.info("No Authentication classes found")
        return

    app['authenticators'] = []
    for auth_class in app['settings'].AUTHENTICATION_CLASSES:
        auth = import_module(auth_class)
        if not issubclass(auth, AbstractAuth):
            _logger.error(f"Class {auth} must be subclass "
                          f"of AbstractAuth")
        app['authenticators'].append(auth(app))
        _logger.info(f"Authenticator '{auth.__name__}' registered")
    _logger.info("Authentication classes registered")
