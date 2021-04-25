import discord
from discord.ext import commands
from models.guild import VoiceConfig
from models.voice import VoiceChannels
from models.types import VoiceType


def setup(bot):
    bot.add_cog(ChannelJoinEvents(bot))


class ChannelJoinEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @property
    def voice_cog(self):
        return self.bot.get_cog("Voice")

    @commands.Cog.listener()
    async def on_normal_channel_join(self, member: discord.Member, config: VoiceConfig):
        memberconfig = await self.voice_cog.fetch_member_config(member)

        name = memberconfig.name or f"{member.name}'s channel"

        bitrate = memberconfig.bitrate or member.guild.bitrate_limit

        limit = memberconfig.limit or 0

        channel = await member.guild.create_voice_channel(
            name=name[:100],
            user_limit=limit,
            category=self.bot.get_channel(config.channel_id).category,
            bitrate=min(bitrate, member.guild.bitrate_limit),
        )

        await VoiceChannels.create(
            id=channel.id,
            owner_id=member.id,
            type=VoiceType.normal,
            channel_id=config.channel_id,
        )
        await member.move_to(channel)

    @commands.Cog.listener()
    async def on_predefined_channel_join(self, member: discord.Member, config: VoiceConfig):
        if member.activity and member.activity.type == discord.ActivityType.playing:
            playing = member.activity.name
        else:
            playing = "nothing"

        memberconfig = await self.voice_cog.fetch_member_config(member)
        channel = await member.guild.create_voice_channel(
            name=config.name.format(username=member.name, game=playing)[:100],
            user_limit=config.limit,
            bitrate=min(memberconfig.bitrate, member.guild.bitrate_limit),
        )

        await VoiceChannels.create(
            id=channel.id,
            owner_id=member.id,
            type=VoiceType.predefined,
            category=self.bot.get_channel(config.channel_id).category,
            channel_id=channel.id,
        )
        await member.move_to(channel)

    @commands.Cog.listener()
    async def on_cloned_channel_join(self, member: discord.Member, config: VoiceConfig):
        channel = self.bot.get_channel(config.channel_id)
        cloned = await channel.clone(name=f"[{channel.name}] {member.name}"[:100])
        await VoiceChannels.create(
            id=cloned.id,
            owner_id=member.id,
            type=VoiceType.cloned,
            channel_id=channel.id,
        )
        await member.move_to(cloned)

    @commands.Cog.listener()
    async def on_sequential_channel_join(self, member: discord.Member, config: VoiceConfig):
        memberconfig = await self.voice_cog.fetch_member_config(member)
        channel = self.bot.get_channel(config.channel_id)
        sequence = await VoiceChannels.filter(channel_id=channel.id).count()
        created = await member.guild.create_voice_channel(
            name=f"{config.name} #{sequence + 1}"[:100],
            user_limit=config.limit,
            category=channel.category,
            bitrate=min(memberconfig.bitrate, member.guild.bitrate_limit),
        )
        await VoiceChannels.create(
            id=created.id,
            owner_id=member.id,
            type=VoiceType.sequential,
            channel_id=channel.id,
            sequence=sequence + 1,
        )
        await member.move_to(created)
        self.bot.get_cog("Dispatcher")._do_resequence(channel.id)
