import inspect, os
import humanize
import discord
from discord.ext import commands
from datetime import datetime


def setup(bot):
    bot.add_cog(General(bot))


class General(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(self.bot, "uptime"):
            self.bot.uptime = datetime.utcnow()

    @commands.command()
    async def ping(self, ctx: commands.Context):
        return await ctx.send(f"Pong! **{self.bot.latency * 1000:.0f} ms**")

    @commands.command()
    async def uptime(self, ctx: commands.Context):
        humanized = humanize.precisedelta(datetime.utcnow() - self.bot.uptime, format="%0.0f")
        return await ctx.send(f"Uptime: **{humanized}**")

    @commands.command()
    async def invite(self, ctx: commands.Context):
        embed = discord.Embed(color=discord.Color.blurple())
        embed.description = f"[Click here]({self.bot.invite_url}) to invite the bot."
        await ctx.send(embed=embed)

    @commands.command()
    async def support(self, ctx: commands.Context):
        invite = "https://discord.gg/4dFZjwr73n"
        embed = discord.Embed(
            title="Need Help?",
            color=discord.Color.blurple(),
        )
        embed.description = f"[Click here]({invite}) to join the support server."
        await ctx.send(embed=embed)

    @commands.command()
    async def source(self, ctx: commands.Context, *, search: str = None):
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
