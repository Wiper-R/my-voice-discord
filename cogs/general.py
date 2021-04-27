from discord.ext import commands
from datetime import datetime
import humanize


def setup(bot):
    bot.add_cog(General(bot))


class General(commands.Cog):
    def __init__(self, bot):
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
