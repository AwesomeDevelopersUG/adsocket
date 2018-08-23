import logging
from aiohttp import web
import json
import aiohttp

from ..core.message import Message
from .client import Client

_logger = logging.getLogger(__name__)


async def ws_handler(request, **kwargs):

    ws = web.WebSocketResponse(autoping=True, heartbeat=5.0)
    await ws.prepare(request)
    c = Client(ws=ws)
    await request.app['client_pool'].append(c)

    try:
        async for msg in ws:
            print("=" * 100)
            print(msg)
            print("=" * 100)
            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                except Exception as e:
                    await ws.send_json({"error": "decode_error"})
                else:
                    message = Message.from_json(data)
                    print(message)
                    command = request.app['commander'].get(message.type)
                    await command.execute(c, message)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                # print('ws connection closed with exception %s' %
                #       ws.exception())
                msg = f"ws connection closed with exception {ws.exception()}"
                _logger.error(msg)
            else:
                _logger.error(f"Unknown message type {msg.type}")
        await request.app['client_pool'].remove(c)
        return ws
    except Exception as e:
        await request.app['client_pool'].remove(c)
        _logger.error(ws.exception())
        raise


async def http_handler(request, **kwargs):
    pass