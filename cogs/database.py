from discord.ext import commands
import discord
from helpers import mongo
import typing


def setup(bot):
    bot.add_cog(Database(bot))


class Database(commands.Cog):
    """A helper cog for querying through database."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.mongo = mongo

    async def fetch_guilds(self, guild: discord.Guild, fields: dict = None) -> typing.List[mongo.Guild]:
        data = await mongo.db.guild.find({'guild_id': guild.id, }, fields).to_list(None)
        return [mongo.Guild.build_from_mongo(g) for g in data]

    async def fetch_member(self, member: discord.Member, fields: dict = None) -> mongo.Member:
        return await mongo.Member.find_one({'id': member.id}, fields)

    async def fetch_vc(self, channel: discord.VoiceChannel) -> mongo.VoiceChannel:
        return await mongo.VoiceChannel.find_one({'id': channel.id})

    async def fetch_vcs(self, member: discord.Member) -> typing.List[mongo.VoiceChannel]:
        data = await mongo.db.voice_channel.find({'owner': member.id}).to_list(None)
        return [mongo.VoiceChannel.build_from_mongo(x) for x in data]

    async def update_member(self, member: discord.Member, update: dict):
        return await mongo.db.member.update_one({'_id': member.id}, update)
