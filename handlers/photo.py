"""Обработка фото VK бота: сканирование штрих-кодов + OCR."""

import logging
import aiohttp
from io import BytesIO
from PIL import Image

from vkbottle.bot import Bot, Message

from services.scanner import scan_barcodes
from services.ocr import scan_text_ocr
from handlers.barcode import send_barcode_image
from utils.file_manager import temp_image
from config import OCR_API_KEY

logger = logging.getLogger(__name__)


async def download_photo_from_vk(bot: Bot, photo_data: dict) -> bytes | None:
    """Скачать фото из сообщения VK."""
    try:
        # VK gửi URLs фото в разных размерах, берём самый большой
        url = photo_data.get("url", "")
        if not url:
            # Пробуем sizes
            sizes = photo_data.get("sizes", [])
            if sizes:
                url = sizes[-1].get("url", "")

        if not url:
            return None

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.read()
    except Exception:
        logger.exception("Ошибка скачивания фото из VK")
    return None


def _format_reply(codes: list[str], chosen: str) -> str:
    if len(codes) == 1:
        return f"Найдено:\n\n{chosen}"

    all_codes_text = "\n".join(f"  {c}" for c in codes)
    return (
        f"Найдено (штрих-коды + текст):\n\n"
        f"{all_codes_text}\n\n"
        f"Выбран главный код (самый длинный): {chosen}"
    )


def register(bot: Bot) -> None:
    @bot.on.message(attach="photo")
    async def handle_photo(message: Message):
        user_id = message.from_id
        attachments = message.attachments

        if not attachments:
            return

        # Ищем фото среди вложений
        photo_data = None
        for att in attachments:
            if att.type and att.type.value == "photo":
                photo_data = att.photo
                break

        if not photo_data:
            return

        await message.answer("Обрабатываю фото...")

        photo_bytes = await download_photo_from_vk(bot, photo_data)
        if photo_bytes is None:
            await message.answer("Не удалось скачать фото. Попробуй ещё раз.")
            return

        with temp_image(suffix=".jpg") as photo_path:
            try:
                photo_path.write_bytes(photo_bytes)
                img = Image.open(photo_path)

                # Сканируем штрих-коды
                decoded_objects = scan_barcodes(img)
                barcode_codes = [obj.text for obj in decoded_objects]

                # OCR текста
                ocr_codes = scan_text_ocr(str(photo_path), OCR_API_KEY)

                # Объединяем все найденные коды
                codes = list(dict.fromkeys(barcode_codes + ocr_codes))

                if not codes:
                    await message.answer(
                        "Штрих-коды или текст не найдены на фото.\n"
                        "Попробуй сделать фото чётче."
                    )
                    return

                if barcode_codes:
                    chosen = max(barcode_codes, key=len)
                else:
                    chosen = max(codes, key=len)

                reply = _format_reply(codes, chosen)
                await message.answer(reply)
                await send_barcode_image(bot, user_id, chosen)

            except Exception as e:
                await message.answer("Ошибка при обработке фото.")
                logger.exception("Ошибка обработки фото для user %d", user_id)

    logger.info("Обработчик фото VK зарегистрирован")
