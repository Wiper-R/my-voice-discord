import discord
from discord.ext import commands
from discord.permissions import PermissionOverwrite
from models import VoiceConfig, VoiceChannels
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
        member_config = await self.voice_cog.fetch_member_config(member)
        name = member_config.name or f"{member.name}'s channel"
        bitrate = member_config.bitrate or member.guild.bitrate_limit
        limit = member_config.limit or 0
        overwrites = {discord.Object(id=v): PermissionOverwrite(connect=False) for v in member_config.blocked_users}
        created = await member.guild.create_voice_channel(
            name=name[:100],
            user_limit=limit,
            category=self.bot.get_channel(config.channel_id).category,
            bitrate=min(bitrate, member.guild.bitrate_limit),
            overwrites=overwrites,
        )
        await VoiceChannels.create(
            id=created.id,
            owner_id=member.id,
            type=VoiceType.normal,
            channel_id=config.channel_id,
        )
        await member.move_to(created)

    @commands.Cog.listener()
    async def on_predefined_channel_join(self, member: discord.Member, config: VoiceConfig):
        if member.activity and member.activity.type == discord.ActivityType.playing:
            playing = member.activity.name
        else:
            playing = "nothing"
        member_config = await self.voice_cog.fetch_member_config(member)
        overwrites = {discord.Object(id=v): PermissionOverwrite(connect=False) for v in member_config.blocked_users}
        channel = self.bot.get_channel(config.channel_id)
        created = await member.guild.create_voice_channel(
            name=config.name.format(username=member.name, game=playing)[:100],
            user_limit=config.limit,
            bitrate=min(member_config.bitrate, member.guild.bitrate_limit),
            category=channel.category,
            overwrites=overwrites,
        )
        await VoiceChannels.create(
            id=created.id,
            owner_id=member.id,
            type=VoiceType.predefined,
            channel_id=channel.id,
        )
        await member.move_to(created)

    @commands.Cog.listener()
    async def on_cloned_channel_join(self, member: discord.Member, config: VoiceConfig):
        channel = self.bot.get_channel(config.channel_id)
        overwrites = channel.overwrites
        member_config = await self.voice_cog.fetch_member_config(member)
        overwrites.update(
            {discord.Object(id=v): PermissionOverwrite(connect=False) for v in member_config.blocked_users}
        )
        created = await member.guild.create_voice_channel(
            name=f"[{channel.name}] {member.name}"[:100],
            user_limit=channel.user_limit,
            category=channel.category,
            overwrites=overwrites,
            bitrate=channel.bitrate,
        )
        await VoiceChannels.create(
            id=created.id,
            owner_id=member.id,
            type=VoiceType.cloned,
            channel_id=channel.id,
        )
        await member.move_to(created)

    @commands.Cog.listener()
    async def on_sequential_channel_join(self, member: discord.Member, config: VoiceConfig):
        member_config = await self.voice_cog.fetch_member_config(member)
        channel = self.bot.get_channel(config.channel_id)
        sequence = await VoiceChannels.filter(channel_id=channel.id).count()
        overwrites = {discord.Object(id=v): PermissionOverwrite(connect=False) for v in member_config.blocked_users}
        created = await member.guild.create_voice_channel(
            name=f"{config.name} #{sequence + 1}"[:100],
            user_limit=config.limit,
            category=channel.category,
            bitrate=min(member_config.bitrate, member.guild.bitrate_limit),
            overwrites=overwrites,
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
