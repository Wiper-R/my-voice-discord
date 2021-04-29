from tortoise import models
from tortoise import fields
from .types import VoiceType


class VoiceConfig(models.Model):
    class Meta:
        table = "voice_config"

    id = fields.BigIntField(pk=True)
    guild_id = fields.BigIntField()
    channel_id = fields.BigIntField()
    name = fields.CharField(max_length=100, null=True)
    limit = fields.IntField(default=0)
    type = fields.CharEnumField(VoiceType, default=VoiceType.normal)


class GuildConfig(models.Model):
    class Meta:
        table = "guild_config"

    id = fields.BigIntField(pk=True)
    prefix = fields.CharField(max_length=3)
