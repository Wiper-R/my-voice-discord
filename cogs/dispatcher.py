import functools
import discord
import datetime
from discord.ext import commands
from models.guild import VoiceConfig
from models.voice import VoiceChannels
from discord.ext import tasks
import asyncio
from utils.functions import aenumerate


def setup(bot):
    bot.add_cog(Dispatcher(bot))


class Dispatcher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.voice_cooldowns = {}
        self.pending_tasks = {}
        self.cleaner.start()

    def cog_unload(self):
        self.cleaner.stop()
        return super().cog_unload()

    def is_on_cooldown(self, member: discord.Member):
        now = datetime.datetime.utcnow()
        try:
            return self.voice_cooldowns[member.id] > now, (self.voice_cooldowns[member.id] - now).total_seconds()
        except KeyError:
            return False, None

    def _do_cooldown(self, member: discord.Member, time: float = 30):
        self.voice_cooldowns[member.id] = datetime.datetime.utcnow() + datetime.timedelta(seconds=time)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
    ):
        if after.channel and not member.bot:
            self.bot.dispatch("channel_join", member, after)

        if before.channel:
            self.bot.dispatch("channel_left", member, before)

    @commands.Cog.listener()
    async def on_channel_join(self, member: discord.Member, state: discord.VoiceState):
        cooldown, try_after = self.is_on_cooldown(member)

        config = await VoiceConfig.filter(channel_id=state.channel.id).first()

        if config is None:
            return

        if cooldown:  # Checking If User is on cooldown
            message = f"You are in cooldown, try again in {try_after:.2f}s"
            await member.move_to(None)
            return await member.send(message)

        # Putting User on Cooldown
        self._do_cooldown(member, 20)

        self.bot.dispatch(f"{config.type.value}_channel_join", member, config)

    @commands.Cog.listener()
    async def on_channel_left(self, member: discord.Member, state: discord.VoiceState):
        if len(state.channel.members) > 0:
            return

        channel = await VoiceChannels.filter(id=state.channel.id).first()

        if not channel:
            return

        self.bot.dispatch(f"{channel.type.value}_channel_left", channel)

    @tasks.loop(minutes=1)
    async def cleaner(self):
        async for voice in VoiceChannels.all():
            channel = self.bot.get_channel(voice.id)
            if channel is None or len(channel.members) == 0:
                self.bot.dispatch(f"{voice.type.value}_channel_left", voice)

        for chan_id, task in self.pending_tasks.copy().items():
            if task.done:
                del self.pending_tasks[chan_id]

    @cleaner.before_loop
    async def before_cleaner(self):
        await self.bot.wait_until_ready()

    async def update_sequential_channels(self, channel_id):
        config = await VoiceConfig.filter(channel_id=channel_id).first()

        async for idx, channel in aenumerate(VoiceChannels.filter(channel_id=channel_id).order_by("sequence"), 1):
            if channel.sequence != idx:
                channel.sequence = idx
                await channel.save()

                if self.bot.get_channel(channel.id) is not None:
                    await self.bot.get_channel(channel.id).edit(name=f"{config.name} #{idx}"[:100])

    def _do_resequence(self, channel_id):
        if task := self.pending_tasks.get(channel_id):
            if not task.done:
                task.cancel()

        self.pending_tasks[channel_id] = self.bot.loop.create_task(self.update_sequential_channels(channel_id))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.TextChannel):
        config = await VoiceConfig.filter(channel_id=channel.id).first()
        if config is not None:
            await config.delete()
