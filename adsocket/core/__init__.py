"""
The event loop is setup in this module and made available to the entire
application.

UVLoop is used instead of the default asyncio loop for performance reasons.
"""
import asyncio
import signal
import uvloop

loop = uvloop.new_event_loop()
asyncio.set_event_loop(loop)

loop.add_signal_handler(signal.SIGINT, loop.stop)
