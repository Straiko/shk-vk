"""VK бот для сканирования и генерации штрих-кодов."""

import asyncio
import logging
import os

from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

from handlers import commands, photo, barcode
from utils.rate_limiter import RateLimiter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

BOT_TOKEN = os.getenv("VK_BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("VK_BOT_TOKEN не задан! Создайте .env файл")

bot = Bot(token=BOT_TOKEN)
limiter = RateLimiter(interval_seconds=2)

commands.register(bot)
photo.register(bot)
barcode.register(bot)

if __name__ == "__main__":
    bot.run()
