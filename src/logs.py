import sys

from aiologger import Logger
from aiologger.handlers.streams import AsyncStreamHandler

__all__ = ["applogger", "amologger", "_1clogger"]


handler = AsyncStreamHandler(stream=sys.stdout)

applogger = Logger(name="app", handlers=[handler])
amologger = Logger(name="amo", handlers=[handler])
_1clogger = Logger(name="1c", handlers=[handler])
