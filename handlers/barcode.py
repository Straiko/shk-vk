"""Генерация штрих-кодов VK бота."""

import logging

from vkbottle.bot import Bot, Message

import barcode as barcode_lib
from barcode.writer import ImageWriter

from utils.file_manager import temp_image
from handlers.common import get_photo_data, process_photo

logger = logging.getLogger(__name__)


async def send_barcode_image(bot: Bot, user_id: int, text_to_encode: str) -> None:
    try:
        with temp_image(suffix=".png") as tmp_path:
            code128 = barcode_lib.get_barcode_class("code128")
            my_barcode = code128(text_to_encode, writer=ImageWriter())
            saved_path = my_barcode.save(str(tmp_path.with_suffix("")))

            upload_url = await bot.api.photos.get_messages_upload_server()
            import aiohttp
            async with aiohttp.ClientSession() as session:
                with open(saved_path, "rb") as f:
                    data = aiohttp.FormData()
                    data.add_field("file", f, filename="barcode.png")
                    async with session.post(upload_url.upload_url, data=data) as resp:
                        upload_result = await resp.json()

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

    logger.info("Обработчик генерации штрих-кодов VK зарегистрирован")
