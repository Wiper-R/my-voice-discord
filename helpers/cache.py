from collections import OrderedDict
from functools import _make_key, wraps
from dataclasses import dataclass
import inspect


@dataclass
class CacheInfo:
    hits: int
    missed: int
    maxsize: int
    cursize: int
    typed_cache: bool


def _wrap_and_store_key(cache, key, coro):
    async def func():
        value = await coro
        cache[key] = value
        return value

    return func()


def _wrap_new_coroutine(value):
    async def coroutine():
        return value

    return coroutine()


class RawCache(OrderedDict):
    def __init__(self, maxsize, *args, **kwargs):
        self.__maxsize = maxsize
        super().__init__()

    def __setitem__(self, k, v) -> None:
        super().__setitem__(k, v)

        if self.__maxsize is not None:
            while len(self) > self.__maxsize:
                self.popitem(last=False)


def cache(maxsize=128, typed_cache=False):
    _internal_cache = RawCache(maxsize)
    _stats = CacheInfo(0, 0, maxsize, 0, typed_cache)

    def _get_stats():
        _stats.cursize = len(_internal_cache)
        return _stats

    def decorator(func):
        @ wraps(func)
        def wrapper(*args, **kwargs):
            # I have to ignore self i.e. commands.Cog instance
            _args = tuple([arg for arg in args if 'cogs' not in repr(arg)])
            _key = _make_key(_args, kwargs, typed_cache)
            value = _internal_cache.get(_key)

            if not value:
                _stats.missed += 1
                value = func(*args, **kwargs)
                if inspect.isawaitable(value):
                    return _wrap_and_store_key(_internal_cache, _key, value)

                _internal_cache[_key] = value
                return value

            else:
                _stats.hits += 1
                if inspect.iscoroutinefunction(func):
                    return _wrap_new_coroutine(value)

                return value

        def _invalidate(*args, **kwargs):
            try:
                del _internal_cache[_make_key(args, kwargs, typed_cache)]
                return True
            except KeyError:
                return False

        def _invalidate_containing(key):
            to_remove = []
            for k in _internal_cache.keys():
                if key in k:
                    to_remove.append(k)

            for k in to_remove:
                try:
                    del _internal_cache[k]
                except KeyError:
                    continue

        wrapper.cache = _internal_cache
        wrapper.get_key = lambda *args, **kwargs: _make_key(
            args, kwargs, typed_cache)
        wrapper.invalidate = _invalidate
        wrapper.cache_info = wrapper.cache_stats = _get_stats
        wrapper.invalidate_containing = _invalidate_containing

        return wrapper

    return decorator


# import aiohttp
# import asyncio
# import time

# uri = 'https://nekobot.xyz/api/imagegen?type=clyde&text=This%20is%20Text'
# uri2 = 'https://nekobot.xyz/api/imagegen?type=clyde&text=This%20is%20Tex'

# session = aiohttp.ClientSession()

# loop = asyncio.get_event_loop()


# @ cache(0)
# async def _make_request(uri):
#     res = await session.get(uri)
#     data = await res.json()
#     return data['message']


# t = time.time()


# async def main():
#     for _ in range(10):
#         await _make_request(uri)
#         await _make_request(uri2)

# loop.run_until_complete(main())

# print(time.time() - t)

# print(_make_request.get_info())
