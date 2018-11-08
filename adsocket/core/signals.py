import asyncio
from weakref import WeakValueDictionary, WeakSet

ANY = '__ANY__'


def _make_id(target):
    if hasattr(target, '__func__'):
        return id(target.__self__), id(target.__func__)
    return id(target)


class Signal:

    def __init__(self, name=''):
        self._receivers = []
        self.name = name

    def connect(self, receiver, sender=ANY):
        """

        :param receiver:
        :param sender:
        :return:
        """
        lookup_key = (_make_id(receiver), _make_id(sender))
        self._receivers.append((receiver, lookup_key))

    def disconnect(self, receiver, sender=ANY):
        lookup_key = (_make_id(receiver), _make_id(sender))

        if lookup_key in self._receivers:
            self._receivers.remove(lookup_key)

    async def send(self, sender=ANY, **kwargs):
        """

        :param sender:
        :param kwargs:
        :return:
        """
        for r in self._receivers:
            receiver, lookup_key = r
            if _make_id(sender) == lookup_key[1]:
                asyncio.ensure_future(receiver(sender=sender, **kwargs))


new_broker_message = Signal('broker_message_received')