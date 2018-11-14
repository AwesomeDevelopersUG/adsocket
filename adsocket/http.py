from aiohttp import web


async def ping_handler(request, **kwargs):
    """
    Alive test
    :param request:
    :type request:
    :param kwargs:
    :type kwargs:
    :return:
    :rtype:
    """
    return web.Response(text='pong')
