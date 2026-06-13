"""Конфигурация VK бота."""

import os
from dotenv import load_dotenv

load_dotenv()

VK_BOT_TOKEN = os.getenv("VK_BOT_TOKEN", "")
OCR_API_KEY = os.getenv("OCR_API_KEY", "helloworld")
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "20"))
RATE_LIMIT_SECONDS = int(os.getenv("RATE_LIMIT_SECONDS", "2"))
