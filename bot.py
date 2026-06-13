"""VK бот для сканирования и генерации штрих-кодов."""

import asyncio
import logging
import os

from dotenv import load_dotenv
from vkbottle import Bot, VK
from vkbottle.bot import Message

from handlers import commands, photo, barcode

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

BOT_TOKEN = os.getenv("VK_BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError("VK_BOT_TOKEN не задан!")

bot = Bot(token=BOT_TOKEN)

commands.register(bot)
photo.register(bot)
barcode.register(bot)

async def on_startup(bot: VK):
    try:
        result = await bot.api.request("groups.setLongPollSettings", {
            "group_id": 239550562,
            "enabled": 1,
            "wall_post_new": 0,
            "wall_repost_new": 0,
            "message_new": 1,
            "message_reply_new": 0,
            "message_edit": 0,
            "message_allow": 0,
            "message_deny": 0,
            "photo_new": 0,
            "audio_new": 0,
            "video_new": 0,
        })
        logging.info("LongPoll settings set: %s", result)
    except Exception as e:
        logging.exception("Failed to set LongPoll settings")

if __name__ == "__main__":
    logging.info("Запуск VK бота на Long Poll")
    bot.run(on_startup=on_startup)
