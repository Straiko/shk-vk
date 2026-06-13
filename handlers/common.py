"""Совместные функции для обработки фото и штрих-кодов."""

import logging
import aiohttp
from PIL import Image

from vkbottle.bot import Bot, Message

from services.scanner import scan_barcodes
from services.ocr import scan_text_ocr
from utils.file_manager import temp_image
from config import OCR_API_KEY

logger = logging.getLogger(__name__)


def get_photo_data(message: Message):
    attachments = message.attachments or []
    for att in attachments:
        if hasattr(att, "type") and att.type and "photo" in str(att.type):
            return att.photo
    return None


async def download_photo_from_vk(bot: Bot, photo_data) -> bytes | None:
    try:
        sizes = getattr(photo_data, "sizes", [])
        if not sizes:
            return None
        url = sizes[-1].url if hasattr(sizes[-1], "url") else str(sizes[-1])
        if not url:
            return None
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception:
        logger.exception("Ошибка скачивания фото из VK")
    return None


def format_reply(codes: list[str], chosen: str) -> str:
    if len(codes) == 1:
        return f"Найдено:\n\n{chosen}"
    all_codes_text = "\n".join(f"  {c}" for c in codes)
    return (
        f"Найдено (штрих-коды + текст):\n\n"
        f"{all_codes_text}\n\n"
        f"Выбран главный код (самый длинный): {chosen}"
    )


async def process_photo(bot: Bot, message: Message, photo_data) -> None:
    user_id = message.from_id
    logger.info("Photo scan request from user %d", user_id)
    await message.answer("Обрабатываю фото...")

    photo_bytes = await download_photo_from_vk(bot, photo_data)
    if photo_bytes is None:
        await message.answer("Не удалось скачать фото. Попробуй ещё раз.")
        return

    with temp_image(suffix=".jpg") as photo_path:
        try:
            photo_path.write_bytes(photo_bytes)
            img = Image.open(photo_path)

            decoded_objects = scan_barcodes(img)
            barcode_codes = [obj.text for obj in decoded_objects]
            ocr_codes = scan_text_ocr(str(photo_path), OCR_API_KEY)
            codes = list(dict.fromkeys(barcode_codes + ocr_codes))

            if not codes:
                await message.answer(
                    "Штрих-коды или текст не найдены на фото.\n"
                    "Попробуй сделать фото чётче."
                )
                return

            chosen = max(codes, key=len)
            await message.answer(format_reply(codes, chosen))

            from handlers.barcode import send_barcode_image
            await send_barcode_image(bot, user_id, chosen)

        except Exception:
            await message.answer("Ошибка при обработке фото.")
            logger.exception("Ошибка обработки фото для user %d", user_id)
