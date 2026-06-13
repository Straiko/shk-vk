"""Обработчики команд VK бота."""

import logging
from vkbottle.bot import Bot, Message

logger = logging.getLogger(__name__)

CHANGELOG = (
    "v1.0.0 — Первый запуск VK бота\n"
    "Портировано с Telegram/MAX бота"
)

HELP_TEXT = (
    "Привет! Я умею находить штрих-коды и текст на фото и генерировать новые!\n\n"
    "Читать штрих-коды\n"
    "Просто отправь мне фото.\n"
    "Я найду на нём штрих-коды или текст и выдам результат.\n\n"
    "Создать штрих-код\n"
    "Отправь любой текст (латиницу или цифры), и я сделаю из него штрих-код.\n\n"
    "Команды:\n"
    "/start — приветствие\n"
    "/help — эта справка\n"
    "/version — версия бота"
)


def register(bot: Bot) -> None:
    @bot.on.message(text="/start")
    @bot.on.message(text="/help")
    async def send_welcome(message: Message):
        await message.answer(HELP_TEXT)

    @bot.on.message(text="/version")
    async def send_version(message: Message):
        text = (
            f"Версия бота: 1.0.0 (VK)\n\n"
            f"История изменений:\n{CHANGELOG}"
        )
        await message.answer(text)

    logger.info("Обработчики команд VK зарегистрированы")
