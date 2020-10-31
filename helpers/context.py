import discord
from discord.ext import commands
import asyncio


class Context(commands.Context):
    def __init__(self, **attrs) -> None:
        super().__init__(**attrs)

    async def prompt(self, content=None, embed=None, timeout=60, author_id=None, delete_after=False):
        author_id = author_id or self.author.id

        message = await self.send(content=content, embed=embed)

        confirm = None

        def check(payload):
            nonlocal confirm

            if payload.message_id != message.id or payload.user_id != author_id:
                return False

            codepoint = str(payload.emoji)

            if codepoint == '\N{WHITE HEAVY CHECK MARK}':
                confirm = True
                return True
            elif codepoint == '\N{CROSS MARK}':
                confirm = False
                return True

            return False

        for emoji in ('\N{WHITE HEAVY CHECK MARK}', '\N{CROSS MARK}'):
            await message.add_reaction(emoji)

        try:
            await self.bot.wait_for('raw_reaction_add', check=check, timeout=timeout)
        except asyncio.TimeoutError:
            confirm = None

        try:
            if delete_after:
                await message.delete()
        finally:
            return confirm
