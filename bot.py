from discord.ext import commands
from helpers import context
import discord
import config
import aiohttp
import logging

logger = logging.getLogger('discord')
logger.setLevel(logging.ERROR)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


initial_extension = ['cogs.database', 'cogs.voice', 'cogs.event_handler']

intents = discord.Intents.default()
intents.members = True


class MyVoice(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(command_prefix=self.get_prefix, intents=intents, **kwargs)
        self.logger = logger
        self.session = aiohttp.ClientSession(loop=self.loop)

    async def get_prefix(self, message: discord.Message):
        """Custom Prefixes are not included rn"""
        return config.DEFAULT_PREFIX

    async def process_commands(self, message: discord.Message):
        ctx = await self.get_context(message, cls=context.Context)
        await self.invoke(ctx)

    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        ctx = await self.get_context(message)
        if not ctx.valid:
            return
        await self.process_commands(message)

    async def is_owner(self, user):
        if user.id in config.OWNER_IDS:
            return True

        return super().is_owner(user)


bot = MyVoice()

for ext in initial_extension:
    bot.load_extension(ext)

bot.load_extension('jishaku')


@bot.event
async def on_ready():
    print('Bot is Ready')

bot.run(config.DISCORD_BOT_TOKEN)
