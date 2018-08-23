from abc import ABC, abstractmethod

from aioredis import RedisError

from adsocket.core.exceptions import AuthenticationException
from adsocket.core.message import Message
from adsocket.core.utils import import_module


class AbstractAuth(ABC):

    _app = None

    def __init__(self, app):
        self._app = app

    async def authenticate(self, client, message):
        pass


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


class ZeenrAuth(AbstractAuth):

    async def authenticate(self, client, message):

        try:
            token = message.data.get('token')
            data = await self._app['redis'].execute('get', token)
        except RedisError:
            raise AuthenticationException()
        if not data:
            return False, None
        else:
            return True, data


async def initialize_authentication(app):
    if not app['settings'].AUTHENTICATION_CLASSES:
        return

    app['authenticators'] = []
    for auth_class in app['settings'].AUTHENTICATION_CLASSES:
        auth = import_module(auth_class)
        app['authenticators'].append(auth(app))
