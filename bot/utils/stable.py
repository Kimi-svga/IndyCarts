"""Надёжные функции для работы с сообщениями и колбэками (Fast First)."""

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto
from core.logger import setup_logger

logger = setup_logger()


async def safe_answer(query: CallbackQuery, text: str | None = None, show_alert: bool = False) -> None:
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
    # ==========================================
    # ШАГ 1: ПРОБУЕМ НОВЫЙ (БЫСТРЫЙ) МЕТОД (edit)
    # ==========================================
    try:
        # Если нужно отправить текст, и сообщение уже текстовое
        if not photo_file_id and not query.message.photo:
            await query.message.edit_text(
                text=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
            return  # Сработало! Вышли, старый метод не нужен.

        # Если нужно отправить фото, и сообщение уже с фото
        if photo_file_id and query.message.photo:
            await query.message.edit_media(
                media=InputMediaPhoto(
                    media=photo_file_id, 
                    caption=text, 
                    parse_mode="HTML"
                ),
                reply_markup=markup
            )
            return  # Сработало! Вышли.

        # Если тип сообщения меняется (текст -> фото или фото -> текст) - кидаем ошибку
        raise TelegramBadRequest(message="Changing message type")

    except TelegramBadRequest as e:
        # Если текст не изменился - всё ок, просто выходим
        if "message is not modified" in str(e).lower():
            return
        
        # Если не сработало (например, меняем тип сообщения) - идем в шаг 2
        logger.debug(f"Fast edit failed, using old method: {e}")
    except Exception as e:
        logger.debug(f"Fast edit error, using old method: {e}")


    # ==========================================
    # ШАГ 2: СТАРЫЙ МЕТОД (delete + send), ЕСЛИ ШАГ 1 УПАЛ
    # ==========================================
    try:
        await query.message.delete()
    except Exception:
        pass

    try:
        if photo_file_id:
            await query.message.answer_photo(
                photo_file_id,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML"
            )
        else:
            await query.message.answer(
                text,
                reply_markup=markup,
                parse_mode="HTML"
            )
    except Exception as e:
        logger.error(f"safe_render (fallback): {e}")


async def safe_send(bot, chat_id: int, text: str, markup: InlineKeyboardMarkup | None = None) -> bool:
    try:
        await bot.send_message(chat_id, text, reply_markup=markup, parse_mode="HTML")
        return True
    except Exception:
        return False
