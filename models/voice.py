from tortoise import models
from tortoise import fields
from .types import VoiceType


class VoiceChannels(models.Model):
    class Meta:
        table = "voice_channels"

    id = fields.BigIntField(pk=True)
    owner_id = fields.BigIntField()
    sequence = fields.IntField(default=0)
    channel_id = fields.BigIntField()
    type = fields.CharEnumField(VoiceType, default=VoiceType.normal)