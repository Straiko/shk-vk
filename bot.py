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
PORT = int(os.getenv("PORT", "3000"))

if not BOT_TOKEN:
    raise RuntimeError("VK_BOT_TOKEN не задан!")

bot = Bot(token=BOT_TOKEN)

commands.register(bot)
photo.register(bot)
barcode.register(bot)

async def handle_index(request: web.Request):
    return web.Response(text="VK Bot is running")

async def handle_callback(request: web.Request):
    try:
        data = await request.json()
    except Exception:
        logging.exception("Failed to parse JSON")
        return web.Response(text="error")

    logging.info("VK event: %s", json.dumps(data, ensure_ascii=False)[:200])
    event_type = data.get("type")

    if event_type == "confirmation":
        logging.info("Confirmation requested, returning: %s", CONFIRMATION_CODE)
        return web.Response(text=CONFIRMATION_CODE)

    try:
        await bot.process_event(data)
    except Exception as e:
        logging.exception("Ошибка обработки события VK")

    return web.Response(text="ok")

app = web.Application()
app.router.add_get("/", handle_index)
app.router.add_post("/callback", handle_callback)

if __name__ == "__main__":
    logging.info("Запуск VK бота на Callback API, порт %d", PORT)
    logging.info("Confirmation code: %s", CONFIRMATION_CODE)
    web.run_app(app, host="0.0.0.0", port=PORT)
