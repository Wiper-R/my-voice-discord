import re
from discord import AsyncWebhookAdapter, Webhook as webhook_discord


class Webhook:
    @staticmethod
    def get(url: str, session):
        """

        :rtype: Webhook
        """
        webhook_id = int(re.search(r'\d+', url).group())
        webhook_token = re.search(r'(?!.*\/)+(.*)', url).group()
        webhook = webhook_discord.partial(webhook_id, webhook_token, adapter=AsyncWebhookAdapter(
            session=session))
        return webhook
