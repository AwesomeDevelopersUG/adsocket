

class CommandException(Exception):
    """
    Base Command exception
    """
    pass


class CommandNotFoundException(CommandException):
    """
    Raise when command type was not found
    """
    pass


class CommandExecuteError(CommandException):
    """
    Raise when command execution failed
    """
    pass


class CommandNotInitializer(CommandException):
    """
    Raise when command execition was tried to early and command is
    not initialized yet
    """
    pass
