

class CommandException(Exception):
    pass


class CommandNotFoundException(CommandException):
    pass


class CommandExecuteError(CommandException):
    pass

