from cogs.database import Database
from discord.ext import commands
import discord
import textwrap
import traceback
import datetime
from helpers.webhook import Webhook
from .help import MyHelpCommand


def setup(bot):
    bot.add_cog(EventHandler(bot))


class EventHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.help_command = MyHelpCommand()
        self.error_webhook = Webhook.get(
            'https://discord.com/api/webhooks/772023679693488159/n9JNw6NFlE5MfdXbfBNAUu7LmEW5mVfSB7Q7CahOnzKS5G8ugs8hlKq7EZwuZFdfQ44c', bot.session)

    @property
    def db(self) -> Database:
        return self.bot.get_cog('Database')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if after.channel:
            self.bot.dispatch('channel_join', member, after)
        if before.channel:
            self.bot.dispatch('channel_left', member, before)

    @commands.Cog.listener()
    async def on_channel_join(self, member: discord.Member, after: discord.VoiceState):
        guilds = await self.db.fetch_guilds(member.guild)

        if not guilds:
            return

        if not member.guild.me.guild_permissions.manage_channels:
            return

        for channel in guilds:
            if channel.channel != after.channel.id:
                continue

            if channel.type == 1:
                self.bot.dispatch('normal_channel_join', member, after.channel)

            elif channel.type == 2:
                self.bot.dispatch(
                    'sequential_channel_join',
                    member, after.channel)

            elif channel.type == 3:
                self.bot.dispatch(
                    'predefined_channel_join',
                    member, after.channel)

    @commands.Cog.listener()
    async def on_channel_left(self, member: discord.Member, before: discord.VoiceState):
        voice_channel = await self.bot.mongo.VoiceChannel.find_one({'id': before.channel.id})
        if not voice_channel:
            return

        if len(before.channel.members):
            return

        await self.bot.mongo.db.voice_channel.delete_one({'id': before.channel.id})

        if voice_channel.type in [1, 3]:
            self.bot.dispatch(
                'normal_channel_left',
                member, before.channel
            )

        else:
            self.bot.dispatch(
                'sequential_channel_left',
                member, before.channel
            )

    @commands.Cog.listener()
    async def on_normal_channel_join(self, member: discord.Member, channel: discord.VoiceChannel):
        member_settings = await self.db.fetch_member(member)

        if not member_settings:
            member_settings = self.bot.mongo.Member(id=member.id)
            await member_settings.commit()
        name = member_settings.voice_name or member.name

        limit = member_settings.voice_limit or 0
        _perms = discord.Permissions.all()
        bot_perms = {}

        for x, y in _perms:
            bot_perms[x] = y

        overwrites = {
            member.guild.me: discord.PermissionOverwrite(**bot_perms),
            member: discord.PermissionOverwrite(read_messages=True)
        }

        bitrate = member_settings.voice_bitrate or member.guild.bitrate_limit

        reason = f'Created a temporary voice channel for {member} (ID: {member.id})'
        channel = await member.guild.create_voice_channel(name=name, overwrites=overwrites, category=channel.category, bitrate=bitrate, user_limit=limit, reason=reason)
        await member.edit(voice_channel=channel)
        await self.bot.mongo.db.voice_channel.insert_one({'_id': channel.id, 'owner': member.id, 'type': 1})

    @commands.Cog.listener()
    async def on_predefined_channel_join(self, member: discord.Member, channel: discord.VoiceChannel):
        name = f'[{channel.name}] {member.name}'
        bitrate = channel.bitrate
        limit = channel.user_limit
        overwrites = channel.overwrites
        reason = f'Created a temporary voice channel for {member} (ID: {member.id})'
        channel = await member.guild.create_voice_channel(name=name, overwrites=overwrites, category=channel.category, bitrate=bitrate, user_limit=limit, reason=reason)
        await member.edit(voice_channel=channel)
        await self.bot.mongo.db.voice_channel.insert_one({'_id': channel.id, 'owner': member.id, 'type': 3})

    @commands.Cog.listener()
    async def on_normal_channel_left(self, member: discord.Member, channel: discord.VoiceChannel):
        await channel.delete(reason=f'Deleted temporary voice channel that was created for {member} (ID: {member.id})')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if not isinstance(error, (commands.CommandInvokeError, commands.ConversionError)):
            return

        if hasattr(error, 'original'):
            error = error.original

        if isinstance(error, (discord.Forbidden, discord.NotFound, commands.CommandNotFound)):
            return

        e = discord.Embed(title='Command Error', colour=0xcc3366)
        e.add_field(name='Name', value=ctx.command.qualified_name)
        e.add_field(name='Author', value=f'{ctx.author} (ID: {ctx.author.id})')

        fmt = f'Channel: {ctx.channel} (ID: {ctx.channel.id})'
        if ctx.guild:
            fmt = f'{fmt}\nGuild: {ctx.guild} (ID: {ctx.guild.id})'

        e.add_field(name='Location', value=fmt, inline=False)
        e.add_field(name='Content', value=textwrap.shorten(
            ctx.message.content, width=512))

        exc = ''.join(traceback.format_exception(
            type(error), error, error.__traceback__, chain=False))
        e.description = f'```py\n{exc}\n```'
        e.timestamp = datetime.datetime.utcnow()
        await self.error_webhook.send(embed=e, username=f'{self.bot.user.name} Errors', avatar_url=self.bot.user.avatar_url)
