from discord.ext import commands
from models import VoiceChannels


def setup(bot):
    bot.add_cog(ChannelLeftEvents(bot))


class ChannelLeftEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener("on_normal_channel_left")
    @commands.Cog.listener("on_predefined_channel_left")
    @commands.Cog.listener("on_cloned_channel_left")
    @commands.Cog.listener("on_sequential_channel_left")
    async def handle_channel_left(self, voice: VoiceChannels):
        channel = self.bot.get_channel(voice.id)
        if channel is not None:
            await channel.delete()
        await voice.delete()

    @commands.Cog.listener()
    async def on_sequential_channel_left(self, voice: VoiceChannels):
        self.bot.get_cog("Dispatcher")._do_resequence(voice.channel_id)
