import os
import discord
from .registry import BaseChannel
import db

class DiscordChannel(BaseChannel):
    name = "discord"

    def __init__(self):
        self._client = None

    async def start(self, on_message):
        token = os.environ["DISCORD_BOT_TOKEN"]
        trigger = os.environ.get("TRIGGER_WORD", "@Andy")
        intents = discord.Intents.default()
        intents.message_content = True
        self._client = discord.Client(intents=intents)

        @self._client.event
        async def on_message(message: discord.Message):
            if message.author.bot:
                return
            text = message.content or ""
            if trigger not in text:
                return
            prompt = text.replace(trigger, "").strip()
            group_id = f"discord:{message.channel.id}"
            db.enqueue(group_id, "discord", str(message.author.id), prompt)

        await self._client.start(token)

    async def send(self, group_id: str, text: str):
        channel_id = int(group_id.split(":")[1])
        channel = self._client.get_channel(channel_id)
        if channel:
            # Discord has a 2000 char limit per message
            for i in range(0, len(text), 2000):
                await channel.send(text[i:i+2000])
