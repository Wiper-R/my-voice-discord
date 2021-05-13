import inspect, os
from models import GuildConfig
from utils.errors import MyVoiceError
import humanize
import discord
from discord.ext import commands
from datetime import datetime
from utils.prompt import Confirm


def setup(bot):
    bot.add_cog(General(bot))


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = datetime.utcnow()

    @commands.command()
    async def ping(self, ctx: commands.Context):
        """Shows the Websocket latency of the bot."""
        return await ctx.send(f"Pong! **{self.bot.latency * 1000:.0f} ms**")

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        """Shows uptime of {self.bot.user.name}"""
        humanized = humanize.precisedelta(datetime.utcnow() - self.bot.uptime, format="%0.0f")
        return await ctx.send(f"Uptime: **{humanized}**")

    @commands.command()
    async def invite(self, ctx: commands.Context):
        """Send the bot's invitation link."""
        embed = discord.Embed(title="Thanks for choosing me.", color=discord.Color.blurple())
        embed.description = f"[Click here]({self.bot.invite_url}) to invite the bot."
        await ctx.send(embed=embed)

    @commands.command()
    async def support(self, ctx: commands.Context):
        """Need support? join our support server."""
        invite = "https://discord.gg/4dFZjwr73n"
        embed = discord.Embed(
            title="Need Help?",
            color=discord.Color.blurple(),
        )
        embed.description = f"[Click here]({invite}) to join the support server."
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx: commands.Context, *, search: str = None):
        """Refer to the source code of the bot commands."""
        source_url = "https://github.com/Wiper-R/my-voice-discord"

        if search is None:
            return await ctx.send(source_url)

        command = self.bot.get_command(search)

        if not command:
            return await ctx.send("Couldn't find that command.")

        src = command.callback.__code__
        filename = src.co_filename
        lines, firstlineno = inspect.getsourcelines(src)

        location = os.path.relpath(filename).replace("\\", "/")

        final_url = f"<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>"
        await ctx.send(final_url)

    @commands.command()
    @commands.has_guild_permissions(manage_messages=True)
    async def setprefix(self, ctx: commands.Context, *, new_prefix: str):
        """Change the prefix for current server."""
        guild_config = await self.bot.get_cog("Voice").fetch_guild_config(ctx.guild)

        if guild_config.prefix.lower() == new_prefix.lower():
            raise MyVoiceError("This is already a prefix for your server.")

        if not (1 <= len(new_prefix) <= 3):
            raise MyVoiceError("The prefix must have 1 character or more and must not exceed 3 characters.")

        confirm = await Confirm(f"Do you really want to change prefix to `{new_prefix}`?").prompt(ctx)

        if confirm is None:
            raise MyVoiceError("Time's up, aborting!")

        elif confirm is False:
            raise MyVoiceError("Ok Aborting!")

        await GuildConfig.filter(id=ctx.guild.id).update(prefix=new_prefix)

        await ctx.send(f"Successfully changed prefix to `{new_prefix}`!")
