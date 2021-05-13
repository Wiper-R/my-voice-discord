from utils.errors import MyVoiceError
from models import VoiceChannels
from discord.ext import commands


def primary_check():
    async def pred(ctx):

        if not ctx.author.voice:
            raise MyVoiceError("You must be in voice channel to use this command.")

        if not ctx.vc:
            raise MyVoiceError("This is not a temporary voice channel.")

        if ctx.vc.owner_id != ctx.author.id:
            raise MyVoiceError("You don't own this channel.")

        return True

    return commands.check(pred)
