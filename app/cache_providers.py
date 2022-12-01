import time
from typing import Callable, Type, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CacheEntry:
    value: Any
    timestamp: int = time.time()


class BaseCacheProvider(ABC):

    def __init__(self, key_func: Callable):
        self.get_key = key_func

    @abstractmethod
    def get_cache(self):
        raise NotImplementedError()

    @abstractmethod
    def get_obj(self, key) :
        raise NotImplementedError()

    @abstractmethod
    def set_obj(self, key, value):
        raise NotImplementedError()


class DictCacheProvider(BaseCacheProvider):

    cache = {}

    def get_cache(self):
        return self.cache

    def get_obj(self, key) -> Optional[CacheEntry]:
        return self.get_cache().get(key)

    def set_obj(self, key, value):
        obj = CacheEntry(value)
        self.get_cache()[key] = obj


def cache(provider: Type[BaseCacheProvider], timeout: int = 86400):

    def decorator(foo: Callable):

        def wrapper(*args, **kwargs):
            key = provider.get_key(*args, **kwargs)
            cached_entry: Optional[CacheEntry] = provider.get_obj(key)
            if cached_entry is not None:
                timestamp = cached_entry.timestamp
                if (time.time() - timestamp) < timeout:
                    print('Данные из кеша')
                    return cached_entry.value

            r = foo(*args, **kwargs)

            provider.set_obj(key, r)
            # cache[key] = {
            #     "timestamp": now,
            #     "value": r
            # }
            return r

        return wrapper

    return decorator
