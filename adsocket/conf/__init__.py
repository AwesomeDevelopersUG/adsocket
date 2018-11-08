import importlib
import logging
from os import environ

from . import default_settings


_logger = logging.getLogger(__name__)


class Expando:
    """
    A simple expando class to be used as a container for attributes
    """
    pass

    def __init__(self):
        self._vals = dict()

    def __setitem__(self, key, value):
        self._vals[key] = value

    def __getitem__(self, item):
        return self._vals[item]

    def __contains__(self, item):
        return item in self._vals

    def get(self, item, default=None):
        return self._vals.get(item, default)


def load_settings():
    """
    This will load the application defaults first and then set custom settings,
    if the `ADSOCKET_SETTINGS` environment variable is set and pointing to a
    importable Python module

    :return sraps.core.Expando: The combined setting object instance
    """
    # Load defaults
    result = Expando()

    def load_module(module, result_object):
        """
        Iterates over module items, uppercased ones are considered to be a
        setting value. Those are taken an set onto the `result_object` as
        attributes.

        :param module module: An imported python module, we try to load settings
            from
        :param sraps.core.Expando result_object: A object to set the values on
        :return sraps.core.Expando: A simple object containing values as
            attributes
        """

        for key, value in module.__dict__.items():
            if not key.isupper():
                continue

            setattr(result_object, key, value)
        return result_object

    result = load_module(default_settings, result)

    # Try to lookup custom settings file
    if environ.get('ADSOCKET_SETTINGS') is not None:
        try:
            _logger.info("Using settings: {}".format(
                environ.get('ADSOCKET_SETTINGS')))
            mod = importlib.import_module(environ.get('ADSOCKET_SETTINGS'))
            result = load_module(mod, result)
        except ImportError as e:
            msg = "Could not import the settings file: {}".format(e)
            _logger.critical(msg)
            return False
    return result

app_settings = load_settings()
"""
Load settings on import
"""