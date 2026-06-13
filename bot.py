"""VK бот для сканирования и генерации штрих-кодов."""

import logging
import os

from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

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
barcode.register(bot)
photo.register(bot)

if __name__ == "__main__":
    logging.info("Запуск VK бота на Long Poll")
    bot.run()
