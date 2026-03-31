import os
from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from .registry import BaseChannel
import db

class SlackChannel(BaseChannel):
    name = "slack"

    def __init__(self):
        self._app = None

    async def start(self, on_message):
        bot_token = os.environ["SLACK_BOT_TOKEN"]
        app_token = os.environ["SLACK_APP_TOKEN"]
        trigger = os.environ.get("TRIGGER_WORD", "@Andy")
        self._app = AsyncApp(token=bot_token)

        @self._app.message(trigger)
        async def handle_message(message, say):
            text = message.get("text", "")
            prompt = text.replace(trigger, "").strip()
            group_id = f"slack:{message['channel']}"
            db.enqueue(group_id, "slack", message.get("user", "unknown"), prompt)

        handler = AsyncSocketModeHandler(self._app, app_token)
        await handler.start_async()

    async def send(self, group_id: str, text: str):
        channel_id = group_id.split(":")[1]
        await self._app.client.chat_postMessage(channel=channel_id, text=text)
