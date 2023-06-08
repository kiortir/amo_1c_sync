import sys

from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler

__all__ = ["applogger", "amologger", "_1clogger"]


handler = AsyncStreamHandler(stream=sys.stdout)


applogger = Logger.with_default_handlers(name="app")
amologger = Logger.with_default_handlers(name="amo")
_1clogger = Logger.with_default_handlers(name="1c")
