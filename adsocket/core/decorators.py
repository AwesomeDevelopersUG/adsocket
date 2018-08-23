from adsocket.core.commands import commander, AbstractCommand

__all__ = [
    'register_command'
]


def register_command(name=None):
    """

    :param name:
    :return:
    """
    def wraps(func):
        commander.register(name, func)
        return func

    return wraps