from utils.errors import MyVoiceError
from models.voice import VoiceChannels
from discord.ext import commands


def primary_check():
    async def pred(ctx):
        if not ctx.author.voice:
            raise MyVoiceError("You must be in voice channel to use this command.")

        vc = await VoiceChannels.filter(id=ctx.author.voice.channel.id).first()

        if not vc:
            raise MyVoiceError("This is not a temporary voice channel.")

        if vc.owner_id != ctx.author.id:
            raise MyVoiceError("You don't own this channel.")

        ctx.vc = vc

        return True

    return commands.check(pred)