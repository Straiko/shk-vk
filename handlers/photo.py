"""Обработка фото VK бота."""

import logging

from vkbottle.bot import Bot, Message

logger = logging.getLogger(__name__)


def register(bot: Bot) -> None:
    logger.info("Обработчик фото VK зарегистрирован")
