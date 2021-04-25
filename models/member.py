from tortoise import models
from tortoise import fields


class MemberConfig(models.Model):
    class Meta:
        table = "member_config"

    id = fields.BigIntField(pk=True)  # member_id
    name = fields.CharField(max_length=100, default=None, null=True)
    limit = fields.IntField(default=0)
    bitrate = fields.IntField(default=64000)
