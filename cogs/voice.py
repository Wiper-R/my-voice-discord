import typing
import discord
import asyncio

from discord.ext.commands.errors import NoPrivateMessage
from utils.errors import MyVoiceError
from discord.ext import commands
from models.guild import VoiceConfig
from models.types import VoiceType
from models.member import MemberConfig
from models.voice import VoiceChannels
from utils.checks import primary_check
from discord.ext.commands import bot_has_guild_permissions, has_guild_permissions


def setup(bot):
    bot.add_cog(VoiceCog(bot))


class VoiceCog(commands.Cog, name="Voice"):
    def __init__(self, bot):
        self.bot = bot

    async def cog_before_invoke(self, ctx):
        if ctx.author.voice:
            vc = await VoiceChannels.filter(id=ctx.author.voice.channel.id).first()
        else:
            vc = None

        ctx.vc = vc

    async def cog_check(self, ctx):
        if not ctx.guild:
            raise NoPrivateMessage("These commands can't be used in DMs.")
        return True

    async def fetch_member_config(self, member):
        record = await MemberConfig.filter(id=member.id).first()

        if not record:
            record = MemberConfig(id=member.id)

        return record

    @commands.group(invoke_without_command=False)
    async def voice(self, ctx: commands.Context):
        pass

    @voice.group(invoke_without_command=True)
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def setup(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild
        if ctx.invoked_subcommand is None:
            category = await guild.create_category(name="Voice Channels")
            channel = await category.create_voice_channel("Join To Create")
            await VoiceConfig.create(guild_id=guild.id, channel_id=channel.id, type=VoiceType.normal)
            return await ctx.send("**Successfully created a channel. You can now rename it or do what ever you want.**")

    @setup.command()
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def sequence(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild
        try:
            await ctx.send("**Enter the default name of channels getting created (Ex. Gaming Channel)**")
            name = (
                await self.bot.wait_for(
                    "message",
                    check=lambda msg: msg.author.id == ctx.author.id and msg.channel.id == ctx.channel.id,
                    timeout=60,
                )
            ).content

            await ctx.send(
                "**Enter the default limit for channels getting created (Enter any number between 0-99, 0 means no limit)**"
            )

            limit = int(
                (
                    await self.bot.wait_for(
                        "message",
                        check=lambda msg: msg.author.id == ctx.author.id
                        and msg.channel.id == ctx.channel.id
                        and msg.content.isdigit()
                        and int(msg.content) < 99,
                        timeout=60,
                    )
                ).content
            )

        except asyncio.TimeoutError:
            return await ctx.send("Response timed out!")
        else:
            category = await guild.create_category(name="Sequenced Voice Channels")
            channel = await category.create_voice_channel(name="Join To Create")
            await VoiceConfig.create(
                guild_id=guild.id, channel_id=channel.id, name=name, limit=limit, type=VoiceType.sequential
            )
            return await ctx.send("**Successfully created a channel. You can now rename it or do what ever you want.**")

    @setup.command()
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def clone(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild
        category = await guild.create_category(name="Voice Channels")
        channel = await category.create_voice_channel(name="Join To Create")
        await VoiceConfig.create(guild_id=guild.id, channel_id=channel.id, type=VoiceType.cloned)
        return await ctx.send(
            "**Successfully setup a cloned channel.\nYou can now modify it according to your wants.**"
        )

    @setup.command()
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def predefined(self, ctx: commands.Context):
        guild: discord.Guild = ctx.guild
        try:
            await ctx.send(
                "**Enter the default name of channel getting created:**\nUse {username} in order to replace that with username while creating channel. Ex: {username}'s lounge\nUse {game} inorder to replace that with game that user is playing. Ex {username}'s playing {game}"
            )
            name = (
                await self.bot.wait_for(
                    "message", check=lambda msg: msg.channel == ctx.channel and msg.author == ctx.author, timeout=60
                )
            ).content

            await ctx.send(
                "**Enter the default limit of channel getting created. (A Number between 0-99, 0 means no limit)**"
            )
            limit = int(
                (
                    await self.bot.wait_for(
                        "message",
                        check=lambda msg: msg.channel == ctx.channel
                        and msg.author == ctx.author
                        and msg.content.isdigit()
                        and int(msg.content) < 99,
                        timeout=60,
                    )
                ).content
            )
        except asyncio.TimeoutError:
            return await ctx.send("Response timed out!")
        else:
            category = await guild.create_category(name="Voice Channels")
            channel = await category.create_voice_channel(name="Join To Create")
            await VoiceConfig.create(
                guild_id=guild.id, channel_id=channel.id, type=VoiceType.predefined, name=name, limit=limit
            )
            await ctx.send("**You are all setup and ready to go!**")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def name(self, ctx: commands.Context, *, new_name: str):
        if ctx.vc.type != VoiceType.normal:
            return await ctx.send("You can't edit the name this channel.")

        if len(new_name) > 100:
            raise MyVoiceError("Name must not exceed 100 characters.")

        config = await self.fetch_member_config(ctx.author)
        config.name = new_name
        await config.save()
        await ctx.author.voice.channel.edit(name=new_name)
        await ctx.send(f"You successfully changed channel name to '{new_name}'")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def limit(self, ctx: commands.Context, *, new_limit: int):
        if ctx.vc.type == VoiceType.cloned:
            return await ctx.send("You can't edit the limit of this channel.")

        if new_limit < 0 or new_limit > 99:
            return await ctx.send("Limit must be in between 0-99, 0 means no limit.")

        config = await self.fetch_member_config(ctx.author)
        config.limit = new_limit
        await config.save()
        await ctx.author.voice.channel.edit(user_limit=new_limit)
        await ctx.send(f"You successfully changed channel's user limit to '{new_limit}'.")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def bitrate(self, ctx: commands.Context, *, bitrate: int):
        guild = ctx.guild

        if bitrate < 8 or bitrate > guild.bitrate_limit:
            return await ctx.send(f"Bitrate must be in between 8-{guild.bitrate_limit}.")

        config = await self.fetch_member_config(ctx.author)
        config.bitrate = bitrate * 1000
        await config.save()
        await ctx.author.voice.channel.edit(bitrate=config.bitrate)
        await ctx.send(f"You successfully changed channel's bitrate to '{bitrate}'.")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def lock(self, ctx: commands.Context):
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        if overwrite.connect is False:
            return await ctx.send("This channel is already locked! 🔒")

        overwrite.connect = False

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} Voice chat locked! 🔒")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def unlock(self, ctx: commands.Context):
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrite = channel.overwrites_for(role)

        if overwrite.connect is True:
            return await ctx.send(f"{ctx.author.mention} Your channel is already unlocked! 🔓")

        overwrite.connect = True

        await channel.set_permissions(role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} Voice chat unlocked! 🔓")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def ghost(self, ctx: commands.Context):
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrite = channel.overwrites_for(role)

        if overwrite.read_messages is False:
            return await ctx.send(f"{ctx.author.mention} Your voice channel is already invisible! 👻")

        overwrite.read_messages = False
        await channel.set_permissions(role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention}  Your voice channel is now Invisible! 👻")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def unghost(self, ctx: commands.Context):
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrite = channel.overwrites_for(role)
        if overwrite.read_messages is True:
            return await ctx.channel.send(f"{ctx.author.mention} Your voice channel is already visible! 👻")

        overwrite.read_messages = True
        await channel.set_permissions(role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} Voice chat is now Visible! 👻")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def ghostmen(self, ctx: commands.Context, member_or_role: typing.Union[discord.Member, discord.Role]):
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(member_or_role)
        if overwrite.read_messages is True:
            return await ctx.channel.send(
                f"{ctx.author.mention} Your voice channel is already visible for {member_or_role.name}! 👻",
            )

        overwrite.read_messages = True
        await channel.set_permissions(member_or_role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} You have permited {member_or_role.name} to view your channel. ✅")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def permit(self, ctx: commands.Context, member_or_role: typing.Union[discord.Member, discord.Role]):
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(member_or_role)
        if overwrite.connect is True:
            return await ctx.channel.send(
                f"{ctx.author.mention} {member_or_role.name} has already access to your channel ✅."
            )
        overwrite.connect = True
        await channel.set_permissions(member_or_role, overwrite=overwrite)
        await ctx.channel.send(
            f"{ctx.author.mention} You have permitted {member_or_role.name} to have access to the channel. ✅"
        )

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def reject(self, ctx: commands.Context, member_or_role: typing.Union[discord.Member, discord.Role]):
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(member_or_role)
        if overwrite.connect is False:
            return await ctx.send(f"{ctx.author.mention} {member_or_role} has no access to your channel! ❌")
        overwrite.connect = False
        await channel.set_permissions(member_or_role, overwrite=overwrite)
        await ctx.channel.send(
            f"{ctx.author.mention} You have rejected {member_or_role.name} to have access to the channel! ❌"
        )

    @voice.command()
    async def claim(self, ctx):
        if ctx.author.voice is None:
            return await ctx.send("You are not in any voice channel.")

        channel = ctx.author.voice.channel

        vc = await VoiceChannels.filter(id=channel.id).first()

        if vc is None:
            return await ctx.send("You can't claim that channel.")

        if vc.owner_id == ctx.author.id:
            return await ctx.send("This channel is already owned by you.")

        owner = self.bot.get_user(vc.owner_id) or await self.bot.fetch_user(vc.owner_id)

        if owner in ctx.author.voice.channel.members:
            return await ctx.send(f"This channel is already owned by {owner}")

        vc.owner_id = ctx.author.id
        await vc.save()
        await ctx.send("Successfully transferred channel ownership to you.")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    async def game(self, ctx: commands.Context):
        if ctx.vc.type != VoiceType.normal:
            return await ctx.send("You can't edit the name this channel.")

        activity = ctx.author.activity

        if activity is None or not activity.type == discord.ActivityType.playing:
            return await ctx.send("Looks like you aren't playing any game.")

        channel = ctx.author.voice.channel

        if channel.name == activity.name:
            return await ctx.send("Well, your channel has already named as same as your current game name.")

        await channel.edit(name=activity.name)
        await ctx.send(f"Changed your channel name to **{activity.name}**")

    @voice.command()
    @primary_check()
    async def transfer(self, ctx, member: discord.Member):
        """You must own a channel and targeted member should be in that voice channel."""
        if ctx.author == member:
            return await ctx.send("You already own that channel.")

        if member.bot:
            return await ctx.send("You can't transfer owner to a bot.")

        channel = ctx.author.voice.channel

        if member not in channel.members:
            return await ctx.send(f"{member} should be in voice.")

        ctx.vc.owner_id = member.id
        await ctx.vc.save()
        await ctx.send(f"Successfully transferred channel ownership to {member}.")
