import cogs
import discord
from cogs.help import MyHelpCommand
from discord.ext import commands
from utils.errors import MyVoiceError
from discord.ext.commands.errors import (
    BadArgument,
    BotMissingPermissions,
    CommandOnCooldown,
    MissingPermissions,
    MissingRequiredArgument,
    NoPrivateMessage,
)


class MyVoice(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=self.get_prefix, help_command=MyHelpCommand(), **kwargs)

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
            CommandOnCooldown,
        )

        ignorable = ()  # In Development we will not ignore any errors

        if isinstance(error, MyVoiceError) and ctx.command is not None:
            ctx.command.reset_cooldown(ctx)

        if isinstance(error, sendable):
            return await ctx.send(error)

        if isinstance(error, ignorable):
            return

        raise error

    @property
    def invite_url(self):
        return discord.utils.oauth_url(
            self.bot.user.id,
            discord.Permissions(
                manage_channels=True,
                manage_roles=True,
                read_messages=True,
                send_messages=True,
                add_reactions=True,
                move_members=True,
            ),
        )
