from .fields import BigIntArrayField
from tortoise import models, fields
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
    banned_members = BigIntArrayField(default=list)
    prefix = fields.CharField(max_length=3, default="mv!")


class MemberConfig(models.Model):
    class Meta:
        table = "member_config"

    id = fields.BigIntField(pk=True)  # member_id
    name = fields.CharField(max_length=100, default=None, null=True)
    limit = fields.IntField(default=0)
    blocked_users = BigIntArrayField(default=list)
    bitrate = fields.IntField(default=64000)


class VoiceChannels(models.Model):
    class Meta:
        table = "voice_channels"

    id = fields.BigIntField(pk=True)
    owner_id = fields.BigIntField()
    sequence = fields.IntField(default=0)  # This is only usable in sequential channels.
    channel_id = fields.BigIntField()
    type = fields.CharEnumField(VoiceType, default=VoiceType.normal)
