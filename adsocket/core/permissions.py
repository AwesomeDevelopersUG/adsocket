import abc


class Permission(abc.ABC):
    """
    Base permission class. All other permission must instances of this class
    """

    async def can_join(self, channel, client, message):
        pass

    async def can_write(self, channel, client, message):
        pass


class DummyPermission(Permission):
    """
    Dummy permission simply answer to all calls True
    """
    async def can_join(self, channel, client, message):
        return True

    async def can_write(self, channel, client, message):
        return True


class IsAuthenticatedPermission(Permission):
    """
    Check whether client is authenticated.. nothing else
    """
    async def can_join(self, channel, client, message):
        return client.is_authenticated()
