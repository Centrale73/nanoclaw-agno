import os
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
from .registry import BaseChannel
import db

class TelegramChannel(BaseChannel):
    name = "telegram"

    def __init__(self):
        self._app = None

    async def start(self, on_message):
        token = os.environ["TELEGRAM_BOT_TOKEN"]
        trigger = os.environ.get("TRIGGER_WORD", "@Andy")
        self._app = Application.builder().token(token).build()

        async def handler(update: Update, ctx):
            text = update.message.text or ""
            if trigger not in text:
                return
            prompt = text.replace(trigger, "").strip()
            group_id = f"telegram:{update.effective_chat.id}"
            db.enqueue(group_id, "telegram", str(update.effective_user.id), prompt)

        self._app.add_handler(MessageHandler(filters.TEXT, handler))
        await self._app.initialize()
        await self._app.start()
        await self._app.updater.start_polling()

    async def send(self, group_id: str, text: str):
        chat_id = group_id.split(":")[1]
        await self._app.bot.send_message(chat_id=chat_id, text=text)
