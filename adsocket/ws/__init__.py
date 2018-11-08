import logging
from aiohttp import web
import json
import aiohttp

from ..core.message import Message
from .client import Client

_logger = logging.getLogger(__name__)


async def ws_handler(request, **kwargs):
    
    ws = web.WebSocketResponse(autoping=True, heartbeat=5.0)
    try:

        await ws.prepare(request)
    except Exception as e:
        _logger.exception(str(e))
        return ws

    c = Client(ws=ws)
    await request.app['client_pool'].append(c)

    try:
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                # TODO: this is really hack - get rid of it
                if msg.data == 'ping':
                    await ws.send_str('pong')
                    continue

                try:
                    data = json.loads(msg.data)
                except Exception as e:
                    await ws.send_json({"error": "decode_error"})
                    continue
                message = Message.from_json(data)
                command = request.app['commander'].get(message.type)
                try:
                    await command.execute(c, message)
                except Exception as e:
                    _logger.error(f"Error handling command {command}")
                    _logger.exception(str(e))

            elif msg.type == aiohttp.WSMsgType.ERROR:
                # print('ws connection closed with exception %s' %
                #       ws.exception())
                msg = f"Received error {ws.exception()}"
                _logger.error(msg)
            else:
                _logger.error(f"Unknown message type {msg.type}")
    except Exception as e:
        _logger.error(str(e))
    finally:
        return ws


async def http_handler(request, **kwargs):
    pass