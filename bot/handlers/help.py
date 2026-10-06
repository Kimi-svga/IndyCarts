"""/help — список команд по роли игрока."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.utils.decorators import get_user_role

router = Router()


PLAYER_COMMANDS = """
<b>Игроку</b>

/start — регистрация / меню
/menu — главное меню
/profile — профиль
/support — поддержка
/help — эта справка
/promo — активировать промокод

/loan 50000 — взять кредит
/repay 5000 — погасить кредит
/refinance — рефинансировать

/duel @username — вызвать на PvP
"""

MODERATOR_COMMANDS = """
🟡 <b>Модератор</b>

/warn @user причина — предупреждение
/mute @user 24h причина — мьют
/banlist — активные наказания
/banhistory @user — история игрока
/userinfo @user — карточка игрока
/admins — команда проекта
"""

ADMIN_COMMANDS = """
🔴 <b>Администратор</b>

/admin — панель админа
/givecard @user ID — выдать карту
/takecard @user ID — забрать карту
/resetpvp @user — сброс рейтинга

/ban @user 30d причина — бан
/unban @user — снять наказание

/broadcast — рассылка всем
/broadcast_plus — рассылка Indy+
/broadcast_top — топ-10

/announce текст — пост в канал

/stats — общая статистика
/stats_economy — экономика
/stats_cards — карты
/stats_pvp — PvP
/stats_plus — Indy+
/stats_tech — техника

/support_panel — панель поддержки
"""

OWNER_COMMANDS = """
👑 <b>Владелец</b>

/hire @user роль — назначить
/fire @user — снять
/adminrole @user — инфо о роли

/setbalance @user сумма — установить баланс
/addmoney @user сумма — добавить монет
/giveaway @user сумма — подарок

/setseasonreward — награды сезона
/setreward — награды топ
/event ID множитель — событие биржи
"""

SUPPORT_COMMANDS = """
🔵 <b>Поддержка</b>

/support_panel — панель поддержки
/support — помощь игроку
"""


async def _build_help(telegram_id: int) -> str:
    role = await get_user_role(telegram_id)

    header = "📖 <b>Справка Indy Carts</b>\n\n"

    if role is None:
        return (
            header + PLAYER_COMMANDS +
            "\n\n<i>Ты ещё не зарегистрирован. /start</i>"
        )

    parts = [header, PLAYER_COMMANDS]

    if role == "owner":
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(OWNER_COMMANDS)
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(ADMIN_COMMANDS)
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(MODERATOR_COMMANDS)
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(SUPPORT_COMMANDS)
    elif role == "admin":
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(ADMIN_COMMANDS)
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(MODERATOR_COMMANDS)
    elif role == "moderator":
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(MODERATOR_COMMANDS)
    elif role in ("support", "helper"):
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(SUPPORT_COMMANDS)
        parts.append("\n━━━━━━━━━━━━━━━━━━\n")
        parts.append(MODERATOR_COMMANDS)

    parts.append("\n\n<i>Все команды также доступны через кнопки в меню.</i>")

    return "".join(parts)


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = await _build_help(message.from_user.id)

    if len(text) > 4000:
        half = len(text) // 2
        split_at = text.rfind("\n\n", 0, half + 200)
        if split_at == -1:
            split_at = half

        await message.answer(text[:split_at], parse_mode="HTML")
        await message.answer(text[split_at:], parse_mode="HTML")
    else:
        await message.answer(text, parse_mode="HTML") 
