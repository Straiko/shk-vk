"""Генерация штрих-кодов VK бота."""

import asyncio
import logging
import aiohttp

from vkbottle.bot import Bot, Message

import barcode as barcode_lib
from barcode.writer import ImageWriter

from utils.file_manager import temp_image
from utils.db import log_activity
from handlers.common import get_photo_data, process_photo

logger = logging.getLogger(__name__)


async def upload_photo_to_vk(bot: Bot, photo_path: str, max_retries: int = 3) -> str:
    """Загрузить фото в сообщения VK с повторными попытками при сбоях сервера VK."""
    with open(photo_path, "rb") as f:
        file_bytes = f.read()

    for attempt in range(1, max_retries + 1):
        try:
            upload_server = await bot.api.photos.get_messages_upload_server()
            data = aiohttp.FormData()
            data.add_field("photo", file_bytes, filename="barcode.png", content_type="image/png")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    upload_server.upload_url,
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "VK photo upload вернул статус %d (попытка %d/%d)",
                            resp.status,
                            attempt,
                            max_retries,
                        )
                        await asyncio.sleep(1)
                        continue

                    upload_result = await resp.json(content_type=None)

            if not upload_result or "photo" not in upload_result or upload_result.get("photo") == "[]":
                logger.warning(
                    "VK вернул пустой результат загрузки (попытка %d/%d): %s",
                    attempt,
                    max_retries,
                    upload_result,
                )
                await asyncio.sleep(1)
                continue

            saved_photo = await bot.api.photos.save_messages_photo(
                server=upload_result["server"],
                photo=upload_result["photo"],
                hash=upload_result["hash"],
            )

            if saved_photo:
                return f"photo{saved_photo[0].owner_id}_{saved_photo[0].id}"

        except Exception as e:
            logger.warning(
                "Сбой загрузки фото в VK (попытка %d/%d): %s",
                attempt,
                max_retries,
                e,
            )
            await asyncio.sleep(1)

    raise RuntimeError("Не удалось загрузить фото в VK после повторных попыток")


async def send_barcode_image(bot: Bot, user_id: int, text_to_encode: str) -> None:
    try:
        with temp_image(suffix=".png") as tmp_path:
            code128 = barcode_lib.get_barcode_class("code128")
            my_barcode = code128(text_to_encode, writer=ImageWriter())
            saved_path = my_barcode.save(str(tmp_path.with_suffix("")))

            photo_str = await upload_photo_to_vk(bot, saved_path)

            await bot.api.messages.send(
                user_id=user_id,
                attachment=photo_str,
                message=f"Штрих-код для: {text_to_encode}",
                random_id=0,
            )
    except Exception:
        await bot.api.messages.send(
            user_id=user_id,
            message="Ошибка при генерации штрих-кода.",
            random_id=0,
        )
        logger.exception("Ошибка генерации штрих-кода для user %d", user_id)


def register(bot: Bot) -> None:
    @bot.on.message()
    async def handle_any_message(message: Message):
        photo_data = get_photo_data(message)
        if photo_data:
            await process_photo(bot, message, photo_data)
            return

        text_to_encode = message.text.strip() if message.text else ""
        if not text_to_encode or text_to_encode.startswith("/"):
            return

        user_id = message.from_id
        logger.info("Barcode request from user %d: %s", user_id, text_to_encode)

        if not all(c.isascii() and (c.isalnum() or c in "-_") for c in text_to_encode):
            await message.answer(
                "Для генерации штрих-кода используй латиницу или цифры.\n"
                "Например: ii424124"
            )
            return

        await send_barcode_image(bot, user_id, text_to_encode)
        log_activity(user_id, None, None, None, "barcode_generated", text_to_encode)

    logger.info("Обработчик генерации штрих-кодов VK зарегистрирован")
