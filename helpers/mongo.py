from umongo import instance, fields, Document
from motor.motor_asyncio import AsyncIOMotorClient
import config

db = AsyncIOMotorClient(config.DATABASE_URL)[config.DATABASE_NAME]


instance = instance.Instance(db)


@instance.register
class Member(Document):
    id = fields.IntegerField(attribute='_id')
    voice_name = fields.StrField(default=None)
    voice_limit = fields.IntegerField(default=0)
    voice_bitrate = fields.IntegerField(default=None)


@instance.register
class VoiceChannel(Document):
    id = fields.IntegerField(attribute='_id')
    owner = fields.IntegerField()
    type = fields.IntegerField(default=1)


@instance.register
class Guild(Document):
    id = fields.ObjectIdField(attribute='_id')
    guild_id = fields.IntegerField(required=True)
    channel = fields.IntegerField(required=True)
    type = fields.IntegerField(default=1)
