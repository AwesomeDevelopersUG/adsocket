import logging

from adsocket.core.commands.exceptions import CommandNotFoundException
from .commands import AbstractCommand, AuthenticateCommand, \
    SubscribeCommand, PublishCommand, PingCommand

__all__ = [
    'Commander',
    'commander',
]

_logger = logging.getLogger(__name__)


class Commander:

    def __init__(self):
        self._commands = {}
        self._app = None
        self._known_commands = {}

    def register(self, name: str, command: AbstractCommand):
        if name in self._commands or name in self._known_commands:
            msg = f"Conflict: Command {name} has been already registered"
            raise RuntimeError(msg)
        if self.is_initialized():
            self._initialize_command(name, command)
        else:
            self._known_commands[name] = command

    def is_initialized(self):
        return self._app is not None

    def _initialize(self):
        if not self._app:
            raise RuntimeError("I am not initialized yet")

        for name, command in self._known_commands.items():
            self._initialize_command(name, command)

    def _initialize_command(self, name, klazz):
        _logger.info(f"Initializing command {name}")
        cmd = klazz(app=self._app)
        self._commands[name] = cmd

    def get(self, name):
        if not self._app:
            raise RuntimeError("I am not initialized yet")
        if name not in self._commands:
            known = self._commands.keys()
            raise CommandNotFoundException(f"Unkown command {name}. Known commands are {known}")

        return self._commands[name]

    def set_app(self, app):
        if self._app:
            raise RuntimeError("I already have application")
        self._app = app
        self._initialize()


commander = Commander()

commander.register('authenticate', AuthenticateCommand)
commander.register('subscribe', SubscribeCommand)
commander.register('publish', PublishCommand)
commander.register('ping', PingCommand)
