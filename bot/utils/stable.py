"""Надёжные функции для работы с сообщениями и колбэками."""

from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from core.logger import setup_logger

logger = setup_logger()


async def safe_answer(query: CallbackQuery, text: str | None = None, show_alert: bool = False) -> None:
    """Безопасно отвечает на колбэк."""
    try:
        await query.answer(text=text, show_alert=show_alert)
    except Exception:
        pass


async def safe_render(
    query: CallbackQuery,
    text: str,
    markup: InlineKeyboardMarkup | None = None,
    photo_file_id: str | None = None,
) -> None:
    """Надёжно отображает сообщение. Не падает на 'message is not modified'."""
    if not photo_file_id:
        try:
            await query.message.edit_text(text, reply_markup=markup, parse_mode="HTML")
            return
        except Exception as e:
            if "not modified" in str(e).lower():
                return

    try:
        await query.message.delete()
    except Exception:
        pass

    try:
        if photo_file_id:
            await query.message.answer_photo(photo_file_id, caption=text, reply_markup=markup, parse_mode="HTML")
        else:
            await query.message.answer(text, reply_markup=markup, parse_mode="HTML")
    except Exception as e:
        logger.error(f"safe_render: {e}")


async def safe_send(bot, chat_id: int, text: str, markup: InlineKeyboardMarkup | None = None) -> None:
    """Безопасно отправляет сообщение."""
    try:
        await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
    except Exception:
        pass
