"""Админка VK бота: статистика, активность, пользователи."""

import logging
import os

from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, Callback

from utils.db import (
    init_db, log_activity, get_stats, get_recent_activity,
    get_users, get_activity_by_id, delete_last_activities
)

logger = logging.getLogger(__name__)

ADMIN_USER_ID = int(os.getenv("VK_ADMIN_ID", "0"))


def is_admin(user_id: int) -> bool:
    if not ADMIN_USER_ID or user_id is None:
        return False
    return user_id == ADMIN_USER_ID


def get_admin_keyboard() -> Keyboard:
    kb = Keyboard(inline=True)
    kb.row()
    kb.add(Callback("📊 Статистика", payload={"cmd": "admin_stats"}))
    kb.add(Callback("📝 Действия", payload={"cmd": "admin_activity"}))
    kb.row()
    kb.add(Callback("👥 Пользователи", payload={"cmd": "admin_users"}))
    kb.add(Callback("❌ Закрыть", payload={"cmd": "admin_close"}))
    return kb


def get_back_keyboard() -> Keyboard:
    kb = Keyboard(inline=True)
    kb.row()
    kb.add(Callback("⬅️ В главное меню", payload={"cmd": "admin_main"}))
    return kb


def _format_activity_list(activity: list[dict]) -> tuple[str, Keyboard]:
    if not activity:
        return "📝 Последние действия:\n\nПусто.", get_back_keyboard()

    lines = []
    for a in activity:
        time_str = a['timestamp'][11:19] if a['timestamp'] else "??:??:??"
        name = a.get('first_name') or a.get('username') or "Без имени"
        act_icon = "📷" if "photo" in (a['action'] or "") else "📝"
        details = a.get('details') or "Нет данных"
        lines.append(f"{time_str} | {act_icon} {name[:12]} (#{a['id']})\n  {details}")

    text = "📝 Последние 50 действий:\n\n" + "\n\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n... (обрезано)"

    kb = Keyboard(inline=True)
    kb.row()
    kb.add(Callback("🗑 Очистить последние 5", payload={"cmd": "admin_clear_5"}))
    kb.row()
    kb.add(Callback("⬅️ В главное меню", payload={"cmd": "admin_main"}))
    return text, kb


def register(bot: Bot) -> None:
    init_db()

    @bot.on.message(text="/admin")
    async def send_admin_menu(message: Message):
        user_id = message.from_id
        if not is_admin(user_id):
            await message.answer("⛔ У вас нет доступа.")
            return

        kb = get_admin_keyboard()
        await message.answer(
            "👋 Панель администратора\n\nВыберите нужный раздел:",
            keyboard=kb,
        )

    @bot.on.raw_event("message_event")
    async def handle_admin_callbacks(event):
        obj = event.get("object", {})
        payload = obj.get("payload", {})
        cmd = payload.get("cmd", "")
        user_id = obj.get("user_id", 0)
        peer_id = obj.get("peer_id", 0)

        if not cmd.startswith("admin_"):
            return

        if not is_admin(user_id):
            await bot.api.messages.send(
                peer_id=peer_id,
                message="⛔ Нет доступа.",
                random_id=0,
            )
            return

        action = cmd.replace("admin_", "", 1)

        if action == "close":
            return

        elif action == "main":
            kb = get_admin_keyboard()
            await bot.api.messages.send(
                peer_id=peer_id,
                message="👋 Панель администратора\n\nВыберите нужный раздел:",
                keyboard=kb,
                random_id=0,
            )
            return

        elif action == "stats":
            stats = get_stats()
            text = (
                "📊 Общая статистика:\n\n"
                f"👥 Всего юзеров: {stats['total_users']}\n"
                f"📅 Уникальных сегодня: {stats['today_users']}\n"
                f"🔄 Всего запросов: {stats['total_requests']}\n"
            )
            kb = get_admin_keyboard()
            await bot.api.messages.send(
                peer_id=peer_id,
                message=text,
                keyboard=kb,
                random_id=0,
            )
            return

        elif action == "activity":
            activity = get_recent_activity(50)
            text, kb = _format_activity_list(activity)
            await bot.api.messages.send(
                peer_id=peer_id,
                message=text,
                keyboard=kb,
                random_id=0,
            )
            return

        elif action == "clear_5":
            delete_last_activities(5)
            activity = get_recent_activity(50)
            text, kb = _format_activity_list(activity)
            await bot.api.messages.send(
                peer_id=peer_id,
                message="✅ Удалено!",
                random_id=0,
            )
            await bot.api.messages.send(
                peer_id=peer_id,
                message=text,
                keyboard=kb,
                random_id=0,
            )
            return

        elif action == "users":
            users = get_users(limit=100)
            if not users:
                text = "👥 Последние пользователи:\n\nПусто."
            else:
                lines = []
                for u in users:
                    name = u.get('first_name') or u.get('username') or "Без имени"
                    last_seen = u['last_seen'][11:19] if u.get('last_seen') else "??:??:??"
                    lines.append(f"👤 {name[:15]} | {u['user_id']} | 🕒 {last_seen}")
                text = "👥 Последние 100 заходивших:\n\n" + "\n".join(lines)
                if len(text) > 4000:
                    text = text[:4000] + "\n... (обрезано)"

            kb = get_admin_keyboard()
            await bot.api.messages.send(
                peer_id=peer_id,
                message=text,
                keyboard=kb,
                random_id=0,
            )
            return

    logger.info("Обработчик админки VK зарегистрирован")
