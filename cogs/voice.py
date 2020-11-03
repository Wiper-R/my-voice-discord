from cogs.database import Database
from discord.ext import commands
import discord
import typing


def setup(bot):
    bot.add_cog(Voice(bot))


class NoVoiceChannel(commands.CheckFailure):
    pass


def has_a_channel():
    async def pred(ctx):
        db = ctx.bot.get_cog('Database')
        if not ctx.author.voice:
            raise NoVoiceChannel(
                'You must be in voice channel to use this command.')

        vc = await db.fetch_vc(ctx.author.voice.channel.id)

        if not vc:
            raise NoVoiceChannel("This is not a temporary voice channel.")

        if vc.owner != ctx.author.id:
            raise NoVoiceChannel("You don't own this channel.")

        if vc.type != 1:
            raise NoVoiceChannel(
                "You can't use these command in this channel.")

        return True

    return commands.check(pred)


class Voice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_command_error(self, ctx, error):
        send_back = (
            commands.BadArgument,
            commands.BotMissingPermissions,
            NoVoiceChannel,
            commands.MissingPermissions,
            commands.CommandOnCooldown,
            commands.MissingRequiredArgument,
            NoVoiceChannel,
            discord.Forbidden
        )

        if isinstance(error, commands.CommandOnCooldown):
            return await ctx.send(error)

        if ctx.command is not None:
            await ctx.command.reset_cooldown(ctx)

        if isinstance(error, send_back):
            return await ctx.send(error)

        raise error

    @property
    def db(self) -> Database:
        return self.bot.get_cog('Database')

    @commands.group(invoke_without_command=True)
    async def voice(self, ctx: commands.Context):
        ...

    @voice.group(name="setup", invoke_without_command=True)
    @commands.cooldown(1, per=60, type=commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    async def voice_setup(self, ctx: commands.Context):
        overwrites = {ctx.me: discord.PermissionOverwrite(
            manage_channels=True)}
        category = await ctx.guild.create_category_channel('Voice Channels', overwrites=overwrites)
        channel = await ctx.guild.create_voice_channel('Join To Create', category=category, overwrites=overwrites)

        await self.bot.mongo.Guild(guild_id=ctx.guild.id, channel=channel.id, type=1).commit()
        self.db.fetch_guilds.invalidate(ctx.guild.id)
        return await ctx.send("Successfully created a channel. You can now rename it or do what ever you want.")

    @voice_setup.command(name='predefined')
    @commands.cooldown(1, per=60, type=commands.BucketType.guild)
    @commands.has_guild_permissions(manage_channels=True)
    async def setup_predefined(self, ctx: commands.Context):
        overwrites = {ctx.me: discord.PermissionOverwrite(
            manage_channels=True)}

        category = await ctx.guild.create_category_channel('Predefined Channels', overwrites=overwrites)
        channel = await ctx.guild.create_voice_channel('(Change Me)', category=category, overwrites=overwrites)

        await self.bot.mongo.Guild(guild_id=ctx.guild.id, channel=channel.id, type=3).commit()
        self.db.fetch_guilds.invalidate(ctx.guild.id)
        return await ctx.send("Successfully created a channel. You can now rename it or do what ever you want.")

    @voice.command(name='name')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_name(self, ctx: commands.Context, *, name: str):
        await ctx.author.voice.channel.edit(name=name)
        await ctx.send(f"You successfully changed channel name to '{name}'")
        await self.db.update_member(ctx.author.id, {"$set": {'voice_name': name}})

    @voice.command(name='bitrate')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_bitrate(self, ctx: commands.Context, *, bitrate: int):
        """Changes bit-rate of your voice channel. You must own a voice channel in that server."""
        if 8 > bitrate < 96:
            return await ctx.send("Bit-rate must be in between 8 to 96.")

        bitrate *= 1000
        await ctx.author.voice.channel.edit(bitrate=bitrate)
        await ctx.channel.send(f'{ctx.author.mention} You have changed the bit-rate of this channel. 🔊')
        await self.db.update_member(ctx.author.id, {"$set": {'voice_bitrate': bitrate}})

    @voice.command(name='lock')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_lock(self, ctx: commands.Context):
        """Locks your voice channel for everyone. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        overwrites = channel.overwrites_for(ctx.guild.default_role)
        if not overwrites.connect and overwrites.connect is not None:
            return await ctx.send(f'{ctx.author.mention} Your channel is already locked! 🔒')
        overwrites.connect = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} Voice chat locked! 🔒')

    @voice.command(name='unlock')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_unlock(self, ctx: commands.Context):
        """Unlocks a channel for everyone. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        role = ctx.guild.get_role(ctx.guild.id)
        overwrites = channel.overwrites_for(role)
        if overwrites.connect and overwrites.connect is not None:
            return await ctx.send(f'{ctx.author.mention} Your channel is already unlocked! 🔓')
        overwrites.connect = True
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} Voice chat unlocked! 🔓')

    @voice.command(name='ghost')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_ghost(self, ctx: commands.Context):
        """Makes your channel invisible for everyone. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role
        overwrites = channel.overwrites_for(role)
        if not overwrites.read_messages and overwrites.read_messages is not None:
            return await ctx.send(f'{ctx.author.mention} Your voice channel is already invisible! :ghost:')
        overwrites.read_messages = False
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.send(f'{ctx.author.mention}  Your voice channel is now Invisible! :ghost:')

    @voice.command(name='unghost')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_unghost(self, ctx: commands.Context):
        """Makes your channel visible for everyone. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        role = ctx.guild.default_role

        overwrites = channel.overwrites_for(role)
        if overwrites.read_messages and overwrites.read_messages is not None:
            return await ctx.channel.send(f'{ctx.author.mention} Your voice channel is already visible! :ghost:')
        overwrites.read_messages = True
        await channel.set_permissions(role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} Voice chat is now Visible! :ghost:')

    @voice.command(name='ghostmen', aliases=['ghostmem'], usage='(member/role)')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_ghostmen(self, ctx, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Allows a member/role to view your channel. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        overwrites = channel.overwrites_for(member_or_role)
        if overwrites.read_messages and overwrites.read_messages is not None:
            return await ctx.channel.send(
                f'{ctx.author.mention} Your voice channel is already visible for {member_or_role}! :ghost:')
        overwrites.read_messages = True
        await channel.set_permissions(member_or_role, overwrite=overwrites)
        await ctx.channel.send(f'{ctx.author.mention} You have permited {member_or_role.name} to view your channel. ✅')

    @voice.command(name='permit', aliases=['allow'], usage='(member/role)')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_permit(self, ctx, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Allows a member/role to connect to your channel. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        overwrites = channel.overwrites_for(member_or_role)
        if overwrites.connect and overwrites.connect is not None:
            return await ctx.channel.send(f'{ctx.author.mention} {member_or_role} has already access to your channel ✅.')
        overwrites.connect = True
        await channel.set_permissions(member_or_role, overwrite=overwrites)
        await ctx.channel.send(
            f'{ctx.author.mention} You have permitted {member_or_role.name} to have access to the channel. ✅')

    @voice.command(name='reject', aliases=['deny'], usage='(member/role)')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_reject(self, ctx, member_or_role: typing.Union[discord.Member, discord.Role]):
        """Denies a member/role to connect to your channel. You must own a voice channel in that server."""
        channel = ctx.author.voice.channel
        overwrites = channel.overwrites_for(member_or_role)
        if overwrites.connect and overwrites.connect is not None:
            return await ctx.channel.send(f'{ctx.author.mention} {member_or_role} has no access to your channel :x:.')
        overwrites.connect = False
        await channel.set_permissions(member_or_role, overwrite=overwrites)
        if member_or_role.voice is not None:
            if member_or_role.voice.channel == channel:
                await member_or_role.move_to(channel=None)
        await ctx.channel.send(
            f'{ctx.author.mention} You have rejected {member_or_role.name} to have access to the channel. :x:')

    @voice.command(name='limit', usage='(0-99)')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_limit(self, ctx, limit: int):
        """Sets users limit to your voice channel. You must own a voice channel in that server."""
        if 99 > limit < 0:
            return await ctx.send("Limit must be in between 0 to 99")
        channel = ctx.author.voice.channel
        if limit == channel.user_limit:
            return await ctx.send("This is already limit of your voice channel.")
        await channel.edit(user_limit=limit)
        await ctx.channel.send(f'{ctx.author.mention} You have set the channel limit to be {limit}!')
        await self.db.update_member(ctx.author.id, {"$set": {"voice_limit": limit}})

    @voice.command(name='claim')
    async def voice_claim(self, ctx):
        """What if original owner lefts the channel,
        don't worry claim it and become new owner of that channel.
        You must be in voice channel."""
        if ctx.author.voice is None:
            return await ctx.send("You are not in any voice channel.")
        channel = ctx.author.voice.channel
        vc = await self.db.fetch_vc(channel.id)
        if vc is None:
            return await ctx.send("You can't claim that channel.")

        if vc.owner == ctx.author.id:
            return await ctx.send("This channel is already owned by you.")
        owner = self.bot.get_user(vc.owner) or (await self.bot.fetch_user(vc.owner))
        if owner in ctx.author.voice.channel.members:
            return await ctx.send(f"This channel is already owned by {owner}")

        await self.bot.mongo.db.voice_channel.update_one({'_id': channel.id}, {"$set": {"owner": ctx.author.id}})
        self.db.fetch_vc.invalidate(channel.id)
        await ctx.send("Successfully transferred channel ownership to you.")

    @voice.command(name='game')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_game(self, ctx):
        """Sets game activity as your channel name. You must own a voice channel in that server."""
        if ctx.author.activity is None:
            return await ctx.send("Looks like you aren't playing any game.")

        if not ctx.author.activity.type == discord.ActivityType.playing:
            return await ctx.send("Looks like you aren't playing any game.")

        channel = ctx.author.voice.channel
        if channel.name == ctx.author.activity.name:
            return await ctx.send("Well, your channel has already named as same as your current game name.")
        await channel.edit(name=ctx.author.activity.name)
        await ctx.send(f"Changed your channel name to **{ctx.author.activity.name}**")

    @voice.command(name='transfer', usage='(member)')
    @has_a_channel()
    @commands.cooldown(1, per=60, type=commands.BucketType.user)
    async def voice_transfer(self, ctx, member: discord.Member):
        """You must own a channel and targeted member should be in that voice channel."""
        if ctx.author == member:
            return await ctx.send("You already own that channel.")
        if member.bot:
            return await ctx.send("You can't transfer owner to a bot.")
        channel = ctx.author.voice.channel
        if member not in channel.members:
            return await ctx.send(f"{member} should be in voice.")
        await self.bot.mongo.db.voice_channel.update_one({'_id': channel.id}, {"$set": {'owner': member.id}})
        self.db.fetch_vc.invalidate(channel.id)
        await ctx.send(f'Successfully transferred channel ownership to {member}.')
