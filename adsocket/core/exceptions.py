

class ADSocketException(Exception):
    message = "Internal server error"


class ChannelException(ADSocketException):
    pass


class ChannelNotFoundException(ADSocketException):
    message = "Channel not found"


class InvalidChannelException(ADSocketException):
    message = "Invalid channel"


class AuthenticationException(ADSocketException):
    message = "Authentication error"


class PermissionDeniedException(ADSocketException):
    message = "Permission denied"


class CommandException(ADSocketException):
    message = "General command error"


class CommandNotFoundException(CommandException):
    message = "Command not found"


class CommandExecuteError(CommandException):
    message = "Command execute error"


class ClientException(ADSocketException):
    message = "Client error"

