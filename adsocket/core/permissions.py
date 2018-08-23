import abc


class Permission(abc.ABC):

    # @abc.abstractmethod
    async def can_join(self, channel, client, message):
        pass

    # @abc.abstractmethod
    async def can_write(self, channel, client, message):
        pass


class DummyPermission(Permission):

    async def can_join(self, channel, client, message):
        return True

    async def can_write(self, channel, client, message):
        return True


class UserChannelPermission(Permission):

    async def can_join(self, channel, client, message):

        if not client.profile['id']:
            return False

        return client.profile['id'] == message.channel_id


class CompanyChannelPermission(Permission):

    async def can_join(self, channel, client, message):

        if not client.profile['id'] or not client.profile['company_id']:
            return False

        return client.profile['company_id'] == message.channel_id
