import importlib


def import_module(pth):
    """

    :param pth:
    :return:
    """
    the_module, klazz = pth.rsplit('.', 1)
    the_module = importlib.import_module(the_module)
    class_ptr = getattr(the_module, klazz)

    return class_ptr


def parse_channel(channel):
    parts = channel.split(":")
    if len(parts) != 2:
        return False

    else:
        return parts[0], parts[1]
