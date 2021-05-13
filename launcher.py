import asyncio
import click
import discord
import config
from tortoise import Tortoise
from bot import MyVoice
import os
import logging
from logging.handlers import RotatingFileHandler
import contextlib


@contextlib.contextmanager
def setup_logging():
    try:
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.WARNING)
        logging.getLogger("db_client").setLevel(logging.ERROR)
        logging.getLogger("tortoise").setLevel(logging.ERROR)
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)
        handler = RotatingFileHandler(
            filename="myvoice.log", encoding="utf-8", mode="w", maxBytes=32 * 1024 * 1024, backupCount=5
        )
        log.addHandler(handler)
        yield
    finally:
        handlers = log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            log.removeHandler(hdlr)


def run_bot():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(Tortoise.init(config.TORTOISE_ORM))
    MyVoice(intents=discord.Intents.all()).run(config.TOKEN)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    if ctx.invoked_subcommand is None:
        with setup_logging():
            run_bot()


if __name__ == "__main__":
    main()
