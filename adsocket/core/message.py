import json
import logging

_logger = logging.getLogger(__name__)


class Message:

    type = None
    channel = None
    channel_id = None
    data = None
    kwargs = None
    request_id = None
    _response_data = None
    _response_id = None

    def __init__(self, type, data, request_id=None,
                 channel=None, **kwargs):
        self.type = type
        self.data = data
        self.request_id = request_id
        self.channel = channel
        self.kwargs = kwargs

    def validate(self, data):
        pass

    def can_respond(self):
        return self.request_id is not None

    @classmethod
    def from_json(cls, data):
        t = data.pop('type', None)
        message_data = data.pop('data', None)
        errors = {}
        if not t:
            errors['type'] = "Can not send message without type"
        if not message_data:
            errors['data'] = "Can not send message without data"
        if not isinstance(data, dict):
            errors['data'] = "Data parameter must be object"
        kwargs = dict()
        kwargs['request_id'] = data.pop('request_id', None)
        kwargs['channel'] = data.pop('channel', None)
        kwargs['channel_id'] = data.pop('channel_id', None)
        return cls(t, data=message_data, **kwargs)

    def to_json(self):
        data = {
            'type': self.type,
            'data': self._response_data or self.data
        }
        if self._response_id:
            data['response_id'] = self._response_id
        elif self.request_id:
            data['request_id'] = self.request_id

        if self.channel:
            data['channel'] = self.channel
        if self.channel_id:
            data['channel_id'] = self.channel_id

        return json.dumps(data)

    def set_response(self, data):
        if not self.can_respond():
            return

        self._response_id = self.request_id
        self._response_data = data

    def __getitem__(self, key):
        return self.data[key]

    def __delitem__(self, key):
        del self.data[key]

    def __iter__(self):
        return iter(self.data)
