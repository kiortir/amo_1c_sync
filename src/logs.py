import sys

from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler

__all__ = ["applogger", "amologger", "_1clogger"]


handler = AsyncStreamHandler(stream=sys.stdout)

applogger = Logger(name="app")
applogger.add_handler(handler)
amologger = Logger(name="amo")
amologger.add_handler(handler)
_1clogger = Logger(name="1c")
_1clogger.add_handler(handler)
