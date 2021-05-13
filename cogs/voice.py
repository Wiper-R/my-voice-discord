import typing
import discord
import asyncio
from tortoise.exceptions import DoesNotExist
from utils.functions import safe_int
from discord.ext.commands.errors import NoPrivateMessage
from utils.errors import MyVoiceError
from discord.ext import commands
from models import VoiceConfig, VoiceType, MemberConfig, VoiceChannels, GuildConfig
from utils.checks import primary_check
from discord.ext.commands import bot_has_guild_permissions, has_guild_permissions
from discord.ext.commands.cooldowns import BucketType
from models.functions import ArrayAppend


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
        try:
            return await MemberConfig.get(id=member.id)
        except DoesNotExist:
            return await MemberConfig.create(id=member.id)

    async def fetch_guild_config(self, guild):
        try:
            return await GuildConfig.get(id=guild.id)
        except DoesNotExist:
            return await GuildConfig.create(id=guild.id)

    @commands.group(invoke_without_command=False)
    async def voice(self, ctx: commands.Context):
        pass

    @voice.group(invoke_without_command=True)
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def setup(self, ctx: commands.Context):
        """Sets a regular 'Join To Create' channel that can be modified by its owner."""
        guild: discord.Guild = ctx.guild
        if ctx.invoked_subcommand is None:
            category = await guild.create_category(name="Voice Channels")
            channel = await category.create_voice_channel("Join To Create")
            await VoiceConfig.create(guild_id=guild.id, channel_id=channel.id, type=VoiceType.normal)
            await ctx.send("**Successfully created a channel. You can now rename it or do what ever you want.**")

    @setup.command()
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def sequence(self, ctx: commands.Context):
        """
        Sets a sequential 'Join To Create' channel, which can be changed by its owner but with some limitations.

        **__Ex.__**
        Gaming #1
        Gaming #2
        """
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
                        and -1 < safe_int(msg.content, -1) < 100,
                        timeout=60,
                    )
                ).content
            )

        except asyncio.TimeoutError:
            raise MyVoiceError("Response timed out!")
        else:
            category = await guild.create_category(name="Sequenced Voice Channels")
            channel = await category.create_voice_channel(name="Join To Create")
            await VoiceConfig.create(
                guild_id=guild.id, channel_id=channel.id, name=name, limit=limit, type=VoiceType.sequential
            )
            await ctx.send("**Successfully created a channel. You can now rename it or do what ever you want.**")

    @setup.command()
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def clone(self, ctx: commands.Context):
        """
        Configuration of a clone channel, which is cloned when a user joins it, anything can be changed in this channel except the name and limit.

        __**Ex**__: `"Channel Name :- PUBG"`, Will create channels as...
        [PUBG] User1
        [PUBG] User2
        """
        guild: discord.Guild = ctx.guild
        category = await guild.create_category(name="Voice Channels")
        channel = await category.create_voice_channel(name="Join To Create")
        await VoiceConfig.create(guild_id=guild.id, channel_id=channel.id, type=VoiceType.cloned)
        await ctx.send("**Successfully setup a cloned channel.\nYou can now modify it according to your wants.**")

    @setup.command()
    @has_guild_permissions(manage_channels=True)
    @bot_has_guild_permissions(manage_channels=True)
    async def predefined(self, ctx: commands.Context):
        """
        Sets a predefined channel, this is similar to cloning but the name and limit are set during configuration.

        __**Ex**__: `"Channel Name :- {username}'s VC, {username} playing {game}"`, Will create channels respectively...
        Wiper's VC
        Wiper playing something
        """
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
                        and -1 < safe_int(msg.content, -1) < 100,
                        timeout=60,
                    )
                ).content
            )
        except asyncio.TimeoutError:
            raise MyVoiceError("Response timed out!")
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
    @commands.cooldown(1, 30, BucketType.user)
    async def name(self, ctx: commands.Context, *, new_name: str):
        """Changes the name of temporary voice channel."""
        if ctx.vc.type != VoiceType.normal:
            raise MyVoiceError("You can't edit the name this channel.")

        if len(new_name) > 100:
            raise MyVoiceError("Name must not exceed 100 characters.")

        channel = ctx.author.voice.channel

        if channel.name == new_name:
            raise MyVoiceError("This is already the name of your channel.")

        config = await self.fetch_member_config(ctx.author)
        config.name = new_name
        await config.save()

        await channel.edit(name=new_name)
        await ctx.send(f"You successfully changed channel name to '{new_name}'")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def limit(self, ctx: commands.Context, *, new_limit: int):
        """Changes the limit of temporary voice channel."""
        if ctx.vc.type == VoiceType.cloned:
            raise MyVoiceError("You can't edit the limit of this channel.")

        if new_limit < 0 or new_limit > 99:
            raise MyVoiceError("Limit must be in between 0-99, 0 means no limit.")

        channel = ctx.author.voice.channel
        if channel.user_limit == new_limit:
            raise MyVoiceError("This is already the limit of your channel.")

        config = await self.fetch_member_config(ctx.author)
        config.limit = new_limit
        await config.save()
        await channel.edit(user_limit=new_limit)
        await ctx.send(f"You successfully changed channel's user limit to '{new_limit}'.")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def bitrate(self, ctx: commands.Context, *, bitrate: int):
        """Changes the bitrate of a voice channel."""
        guild = ctx.guild

        if bitrate < 8 or bitrate > guild.bitrate_limit:
            raise MyVoiceError(f"Bitrate must be in between 8-{guild.bitrate_limit}.")

        channel = ctx.author.voice.channel
        if channel.bitrate == bitrate * 1000:
            raise MyVoiceError("This is already the bitrate of your channel.")

        config = await self.fetch_member_config(ctx.author)
        config.bitrate = bitrate * 1000
        await config.save()
        await channel.edit(bitrate=config.bitrate)
        await ctx.send(f"You successfully changed channel's bitrate to '{bitrate}'.")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def lock(self, ctx: commands.Context):
        """Locks a voice channel for everyone."""
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role)

        if overwrite.connect is False:
            raise MyVoiceError("This channel is already locked! 🔒")

        overwrite.connect = False

        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} Voice chat locked! 🔒")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def unlock(self, ctx: commands.Context):
        """Unlocks a voice channel for everyone."""
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrite = channel.overwrites_for(role)

        if overwrite.connect is True:
            raise MyVoiceError(f"{ctx.author.mention} Your channel is already unlocked! 🔓")

        overwrite.connect = True

        await channel.set_permissions(role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} Voice chat unlocked! 🔓")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def ghost(self, ctx: commands.Context):
        """Hides a voice channel from everyone."""
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrite = channel.overwrites_for(role)

        if overwrite.read_messages is False:
            raise MyVoiceError(f"{ctx.author.mention} Your voice channel is already invisible! 👻")

        overwrite.read_messages = False
        await channel.set_permissions(role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention}  Your voice channel is now Invisible! 👻")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def unghost(self, ctx: commands.Context):
        """Unhides a voice channel from everyone."""
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrite = channel.overwrites_for(role)
        if overwrite.read_messages is True:
            raise MyVoiceError(f"{ctx.author.mention} Your voice channel is already visible! 👻")

        overwrite.read_messages = True
        await channel.set_permissions(role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} Voice chat is now Visible! 👻")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def ghostmen(self, ctx: commands.Context, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Permit a user to see a hidden voice channel."""
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(member_or_role)
        if overwrite.read_messages is True:
            raise MyVoiceError(
                f"{ctx.author.mention} Your voice channel is already visible for {member_or_role.name}! 👻",
            )

        overwrite.read_messages = True
        await channel.set_permissions(member_or_role, overwrite=overwrite)
        await ctx.send(f"{ctx.author.mention} You have permited {member_or_role.name} to view your channel. ✅")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def permit(self, ctx: commands.Context, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Permits a user to join a locked voice channel."""
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(member_or_role)
        if overwrite.connect is True:
            raise MyVoiceError(f"{ctx.author.mention} {member_or_role.name} has already access to your channel ✅.")
        overwrite.connect = True
        await channel.set_permissions(member_or_role, overwrite=overwrite)
        await ctx.channel.send(
            f"{ctx.author.mention} You have permitted {member_or_role.name} to have access to the channel. ✅"
        )

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def reject(self, ctx: commands.Context, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Kicks user from a voice channel and disallows him to join that again."""
        channel = ctx.author.voice.channel
        overwrite = channel.overwrites_for(member_or_role)

        if member_or_role == ctx.author:
            raise MyVoiceError("You can't deny yourself.")

        if overwrite.connect is False:
            raise MyVoiceError(f"{ctx.author.mention} {member_or_role} has no access to your channel! ❌")

        overwrite.connect = False
        await channel.set_permissions(member_or_role, overwrite=overwrite)

        if isinstance(member_or_role, discord.Role):
            role = member_or_role
            for member in channel.members:
                if role in member.roles and member != ctx.author:
                    await member.move_to(None)

        else:
            member = member_or_role
            if member in channel.members:
                await member_or_role.move_to(None)

        await ctx.channel.send(
            f"{ctx.author.mention} You have rejected {member_or_role.name} to have access to the channel! ❌"
        )

    @voice.command()
    @commands.cooldown(1, 30, BucketType.user)
    async def claim(self, ctx):
        """What if actual owner of voice channel lefts?
        No worries you can claim it and make it yours."""
        if ctx.author.voice is None:
            raise MyVoiceError("You are not in any voice channel.")

        vc = ctx.vc

        if vc is None:
            raise MyVoiceError("You can't claim that channel.")

        if vc.owner_id == ctx.author.id:
            raise MyVoiceError("This channel is already owned by you.")

        owner = self.bot.get_user(vc.owner_id) or await self.bot.fetch_user(vc.owner_id)

        if owner in ctx.author.voice.channel.members:
            raise MyVoiceError(f"This channel is already owned by {owner}")

        vc.owner_id = ctx.author.id
        await vc.save()
        await ctx.send("Successfully transferred channel ownership to you.")

    @voice.command()
    @primary_check()
    @bot_has_guild_permissions(manage_channels=True)
    @commands.cooldown(1, 30, BucketType.user)
    async def game(self, ctx: commands.Context):
        """Changes voice channel name to your currently playing game name."""
        if ctx.vc.type != VoiceType.normal:
            raise MyVoiceError("You can't edit the name this channel.")

        activity = ctx.author.activity

        if activity is None or not activity.type == discord.ActivityType.playing:
            raise MyVoiceError("Looks like you aren't playing any game.")

        channel = ctx.author.voice.channel

        if channel.name == activity.name:
            raise MyVoiceError("Well, your channel has already named as same as your current game name.")

        await channel.edit(name=activity.name)
        await ctx.send(f"Changed your channel name to **{activity.name}**")

    @voice.command()
    @primary_check()
    @commands.cooldown(1, 30, BucketType.user)
    async def transfer(self, ctx, member: discord.Member):
        """Transfers voice channel ownership to someone else.
        You must own a channel and targeted member should be in that voice channel."""
        if ctx.author == member:
            raise MyVoiceError("You already own that channel.")

        if member.bot:
            raise MyVoiceError("You can't transfer owner to a bot.")

        channel = ctx.author.voice.channel

        if member not in channel.members:
            raise MyVoiceError(f"{member} should be in voice.")

        ctx.vc.owner_id = member.id
        await ctx.vc.save()
        await ctx.send(f"Successfully transferred channel ownership to {member}.")

    @voice.command()
    @commands.has_guild_permissions(manage_channels=True, manage_roles=True)
    async def ban(self, ctx: commands.Context, member: discord.Member):
        """Bans a member from creating `Join to Create` channel in your server."""
        guild_config = await self.fetch_guild_config(ctx.guild)

        if member.id in guild_config.banned_members:
            raise MyVoiceError(f"{member} is already banned from using JTC channels.")

        await GuildConfig.filter(id=ctx.guild.id).update(banned_members=ArrayAppend("banned_members", member.id))
        await ctx.send(f"Successfully banned {member} from using JTC channels.")

    @voice.command()
    @commands.cooldown(1, 30, BucketType.user)
    async def block(self, ctx: commands.Context, member: discord.Member):
        """Permanently blocks a user from joining your voice channel."""

        if member == ctx.author:
            raise MyVoiceError("You can't block yourself.")

        member_config = await self.fetch_member_config(ctx.author)

        if member.id in member_config.blocked_users:
            raise MyVoiceError(f"{member} is already blocked to join your voice channels.")

        await MemberConfig.filter(id=ctx.author.id).update(blocked_users=ArrayAppend("blocked_users", member.id))
        await ctx.send(f"Successfully blocked {member} to join your voice channels.")
