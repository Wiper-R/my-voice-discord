from discord.ext.commands.errors import (
    BadArgument,
    BotMissingPermissions,
    MissingPermissions,
    MissingRequiredArgument,
    NoPrivateMessage,
)
from utils.errors import MyVoiceError
import discord
from discord.ext import commands
import cogs


class MyVoice(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=self.get_prefix, **kwargs)

        for val in cogs.values:
            self.load_extension(val)

        self.load_extension("jishaku")

    async def get_prefix(self, message):
        return "mv!"

    async def on_ready(self):
        print(f"Logged in as: {self.user}")

    async def on_command_error(self, ctx, error):
        sendable = (
            MyVoiceError,
            BadArgument,
            NoPrivateMessage,
            MissingPermissions,
            MissingRequiredArgument,
            BotMissingPermissions,
        )
        ignorable = ()  # In Development we will not ignore any errors

        if isinstance(error, sendable):
            return await ctx.send(error)

        if isinstance(error, ignorable):
            return

        raise error
