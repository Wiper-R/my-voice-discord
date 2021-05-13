def safe_int(string, default=None):
    try:
        return int(string)
    except ValueError:
        return default


import asyncio
from collections import abc


async def aenumerate(asequence, start=0):
    """Asynchronously enumerate an async iterator from a given start value"""
    n = start
    async for elem in asequence:
        yield n, elem
        n += 1
