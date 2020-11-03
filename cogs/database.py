from discord.ext import commands
import discord
from helpers import mongo
import typing
from helpers import cache


def setup(bot):
    bot.add_cog(Database(bot))


class Database(commands.Cog):
    """A helper cog for querying through database."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bot.mongo = mongo

    @cache.cache(maxsize=None)
    async def fetch_guilds(self, guild_id: int) -> typing.List[mongo.Guild]:
        data = await mongo.db.guild.find({'guild_id': guild_id, }).to_list(None)
        return [mongo.Guild.build_from_mongo(g) for g in data]

    @cache.cache(maxsize=None)
    async def fetch_member(self, member_id: int) -> mongo.Member:
        return await mongo.Member.find_one({'id': member_id})

    @cache.cache(maxsize=None)
    async def fetch_vc(self, channel_id: int) -> mongo.VoiceChannel:
        return await mongo.VoiceChannel.find_one({'id': channel_id})

    @cache.cache(maxsize=None)
    async def fetch_vcs(self, member_id: int) -> typing.List[mongo.VoiceChannel]:
        data = await mongo.db.voice_channel.find({'owner': member_id}).to_list(None)
        return [mongo.VoiceChannel.build_from_mongo(x) for x in data]

    async def update_member(self, member_id: int, update: dict):
        self.fetch_member.invalidate(member_id)
        return await mongo.db.member.update_one({'_id': member_id}, update)
