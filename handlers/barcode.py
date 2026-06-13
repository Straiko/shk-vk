"""Генерация штрих-кодов VK бота."""

import logging
import tempfile
from pathlib import Path

from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text

import barcode as barcode_lib
from barcode.writer import ImageWriter

from utils.file_manager import temp_image

logger = logging.getLogger(__name__)


async def send_barcode_image(bot: Bot, user_id: int, text_to_encode: str) -> None:
    """Сгенерировать Code128 штрих-код и отправить через VK."""
    try:
        with temp_image(suffix=".png") as tmp_path:
            code128 = barcode_lib.get_barcode_class("code128")
            my_barcode = code128(text_to_encode, writer=ImageWriter())
            saved_path = my_barcode.save(str(tmp_path.with_suffix("")))

            # Загружаем фото в VK
            upload_url = await bot.api.photos.get_messages_upload_server()
            import aiohttp
            async with aiohttp.ClientSession() as session:
                with open(saved_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field("file", f, filename="barcode.png")
                    async with session.post(upload_url.upload_url, data=data) as resp:
                        upload_result = await resp.json()

            # Сохраняем фото
            saved_photo = await bot.api.photos.save_messages_photo(
                server=upload_result["server"],
                photo=upload_result["photo"],
                hash=upload_result["hash"],
            )

            photo_str = f"photo{saved_photo[0].owner_id}_{saved_photo[0].id}"
            await bot.api.messages.send(
                user_id=user_id,
                attachment=photo_str,
                message=f"Штрих-код для: {text_to_encode}",
                random_id=0,
            )
    except Exception as e:
        await bot.api.messages.send(
            user_id=user_id,
            message="Ошибка при генерации штрих-кода.",
            random_id=0,
        )
        logger.exception("Ошибка генерации штрих-кода для user %d", user_id)


def register(bot: Bot) -> None:
    @bot.on.message(text="<text:text>")
    async def generate_and_send_barcode(message: Message):
        text_to_encode = message.text.strip()
        if not text_to_encode or text_to_encode.startswith("/"):
            return

        user_id = message.from_id

        # Проверка: текст должен содержать латиницу/цифры
        if not all(c.isascii() and (c.isalnum() or c in "-_") for c in text_to_encode):
            await message.answer(
                "Для генерации штрих-кода используй латиницу или цифры.\n"
                "Например: ii424124"
            )
            return

        await send_barcode_image(bot, user_id, text_to_encode)

    logger.info("Обработчик генерации штрих-кодов VK зарегистрирован")
