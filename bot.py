"""VK бот для сканирования и генерации штрих-кодов."""

import json
import logging
import os

from aiohttp import web
from dotenv import load_dotenv
from vkbottle.bot import Bot, Message

from handlers import commands, photo, barcode

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

BOT_TOKEN = os.getenv("VK_BOT_TOKEN")
CONFIRMATION_CODE = os.getenv("VK_CONFIRMATION", "101e6912")
PORT = int(os.getenv("PORT", "8080"))

if not BOT_TOKEN:
    raise RuntimeError("VK_BOT_TOKEN не задан!")

bot = Bot(token=BOT_TOKEN)

commands.register(bot)
photo.register(bot)
barcode.register(bot)

async def handle_callback(request: web.Request):
    data = await request.json()
    event_type = data.get("type")

    if event_type == "confirmation":
        return web.Response(text=CONFIRMATION_CODE)

    try:
        await bot.process_event(data)
    except Exception as e:
        logging.exception("Ошибка обработки события VK")

    return web.Response(text="ok")

app = web.Application()
app.router.add_post("/callback", handle_callback)

if __name__ == "__main__":
    logging.info("Запуск VK бота на Callback API, порт %d", PORT)
    web.run_app(app, host="0.0.0.0", port=PORT)
