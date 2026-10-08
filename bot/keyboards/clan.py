"""Клавиатуры кланов."""

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.keyboards.main import MainMenu


class ClanMenu(CallbackData, prefix="cln"):
    """Меню клана."""
    action: str
    clan_id: int = 0
    member_id: int = 0
    invite_id: int = 0
    index: int = 0


# ═════════════════════════════════════════════
# ГЛАВНЫЙ ЭКРАН (если не в клане)
# ═════════════════════════════════════════════

def get_no_clan_menu() -> InlineKeyboardMarkup:
    """Меню для игрока без клана."""
    b = InlineKeyboardBuilder()
    b.button(text="🏰 Создать клан", callback_data=ClanMenu(action="create_start").pack())
    b.button(text="🔍 Найти клан", callback_data=ClanMenu(action="search").pack())
    b.button(text="📨 Мои приглашения", callback_data=ClanMenu(action="invites").pack())
    b.button(text="🏆 Топ кланов", callback_data=ClanMenu(action="top").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# МЕНЮ ВНУТРИ КЛАНА
# ═════════════════════════════════════════════

def get_clan_menu(role: str = "member", has_incoming_invites: bool = False) -> InlineKeyboardMarkup:
    """Главное меню клана. Разное для leader/officer/member."""
    b = InlineKeyboardBuilder()

    b.button(text="👥 Участники", callback_data=ClanMenu(action="members").pack())
    b.button(text="💰 Внести вклад", callback_data=ClanMenu(action="deposit").pack())
    b.button(text="📜 История", callback_data=ClanMenu(action="log").pack())
    b.button(text="📊 Статистика", callback_data=ClanMenu(action="stats").pack())

    if role in ("leader", "officer"):
        b.button(text="📨 Пригласить", callback_data=ClanMenu(action="invite").pack())
        if has_incoming_invites:
            b.button(text="📥 Исходящие приглашения", callback_data=ClanMenu(action="outgoing").pack())

    if role == "leader":
        b.button(text="⚙️ Управление", callback_data=ClanMenu(action="manage").pack())

    b.button(text="🚪 Покинуть клан", callback_data=ClanMenu(action="leave_confirm").pack())
    b.button(text="🔙 Назад", callback_data=MainMenu(action="back"))
    b.adjust(2, 2, 1, 1, 1, 1)
    return b.as_markup()


def get_manage_menu() -> InlineKeyboardMarkup:
    """Меню управления кланом (только лидер)."""
    b = InlineKeyboardBuilder()
    b.button(text="👑 Роли", callback_data=ClanMenu(action="roles").pack())
    b.button(text="📝 Описание", callback_data=ClanMenu(action="edit_desc").pack())
    b.button(text="🔓 Открыть/Закрыть", callback_data=ClanMenu(action="toggle_open").pack())
    b.button(text="💥 Распустить клан", callback_data=ClanMenu(action="disband_confirm").pack())
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# УЧАСТНИКИ
# ═════════════════════════════════════════════

def get_members_nav(clan_id: int, index: int, total_pages: int) -> InlineKeyboardMarkup:
    """Навигация по списку участников."""
    b = InlineKeyboardBuilder()
    if index > 0:
        b.button(text="⬅️", callback_data=ClanMenu(action="members", clan_id=clan_id, index=index - 1).pack())
    b.button(text=f"{index + 1}/{total_pages}", callback_data="noop")
    if index < total_pages - 1:
        b.button(text="➡️", callback_data=ClanMenu(action="members", clan_id=clan_id, index=index + 1).pack())
    b.button(text="🔙 К клану", callback_data=ClanMenu(action="menu").pack())
    b.adjust(3, 1)
    return b.as_markup()


def get_member_actions(
    member_id: int,
    role: str,
    viewer_role: str,
) -> InlineKeyboardMarkup:
    """Действия с участником. Зависит от роли смотрящего и целевого."""
    b = InlineKeyboardBuilder()

    can_manage = False
    if viewer_role == "leader" and role != "leader":
        can_manage = True
    elif viewer_role == "officer" and role == "member":
        can_manage = True

    if can_manage:
        if role == "member":
            b.button(
                text="⬆️ Повысить до офицера",
                callback_data=ClanMenu(action="promote", member_id=member_id).pack(),
            )
        elif role == "officer":
            b.button(
                text="⬇️ Понизить до участника",
                callback_data=ClanMenu(action="demote", member_id=member_id).pack(),
            )
        b.button(
            text="🚪 Исключить",
            callback_data=ClanMenu(action="kick_confirm", member_id=member_id).pack(),
        )

    b.button(text="🔙 К участникам", callback_data=ClanMenu(action="members").pack())
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# ВКЛАД
# ═════════════════════════════════════════════

def get_deposit_menu() -> InlineKeyboardMarkup:
    """Быстрые суммы для вклада."""
    b = InlineKeyboardBuilder()
    b.button(text="1 000", callback_data=ClanMenu(action="deposit_go", index=1000).pack())
    b.button(text="5 000", callback_data=ClanMenu(action="deposit_go", index=5000).pack())
    b.button(text="10 000", callback_data=ClanMenu(action="deposit_go", index=10000).pack())
    b.button(text="50 000", callback_data=ClanMenu(action="deposit_go", index=50000).pack())
    b.button(text="✏️ Своя сумма", callback_data=ClanMenu(action="deposit_custom").pack())
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="menu").pack())
    b.adjust(2, 2, 1, 1)
    return b.as_markup()


# ═════════════════════════════════════════════
# ПОДТВЕРЖДЕНИЯ
# ═════════════════════════════════════════════

def get_leave_confirm() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="✅ Да, выйти", callback_data=ClanMenu(action="leave").pack())
    b.button(text="🔙 Отмена", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_disband_confirm() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="💥 Да, распустить", callback_data=ClanMenu(action="disband").pack())
    b.button(text="🔙 Отмена", callback_data=ClanMenu(action="manage").pack())
    b.adjust(1)
    return b.as_markup()


def get_kick_confirm(member_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(
        text="🚪 Да, исключить",
        callback_data=ClanMenu(action="kick", member_id=member_id).pack(),
    )
    b.button(text="🔙 Отмена", callback_data=ClanMenu(action="members").pack())
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# СОЗДАНИЕ (FSM)
# ═════════════════════════════════════════════

def get_create_cancel() -> InlineKeyboardMarkup:
    """Отмена создания клана."""
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_create_confirm() -> InlineKeyboardMarkup:
    """Подтверждение создания клана."""
    b = InlineKeyboardBuilder()
    b.button(text="✅ Создать", callback_data=ClanMenu(action="create_confirm").pack())
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_skip_desc() -> InlineKeyboardMarkup:
    """Пропустить описание."""
    b = InlineKeyboardBuilder()
    b.button(text="⏭ Пропустить", callback_data=ClanMenu(action="create_skip_desc").pack())
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


# ═════════════════════════════════════════════
# ПОИСК / ТОП / ПРИГЛАШЕНИЯ
# ═════════════════════════════════════════════

def get_search_cancel() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_search_results(clans: list, index: int = 0) -> InlineKeyboardMarkup:
    """Результаты поиска — список кликов по кланам."""
    b = InlineKeyboardBuilder()
    for c in clans[:10]:
        b.button(
            text=f"[{c.tag}] {c.name} · ур.{c.level}",
            callback_data=ClanMenu(action="view", clan_id=c.id).pack(),
        )
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_clan_view(clan_id: int, is_open: bool, already_in_clan: bool = False) -> InlineKeyboardMarkup:
    """Просмотр чужого клана."""
    b = InlineKeyboardBuilder()
    if not already_in_clan:
        if is_open:
            b.button(
                text="📥 Вступить",
                callback_data=ClanMenu(action="join", clan_id=clan_id).pack(),
            )
        else:
            b.button(
                text="🔒 Клан закрыт",
                callback_data="noop",
            )
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="search").pack())
    b.adjust(1)
    return b.as_markup()


def get_top_nav() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_invites_menu(invites: list) -> InlineKeyboardMarkup:
    """Список входящих приглашений."""
    b = InlineKeyboardBuilder()
    for invite, clan, from_user in invites[:10]:
        b.button(
            text=f"📨 [{clan.tag}] {clan.name} от @{from_user.username}",
            callback_data=ClanMenu(action="invite_view", invite_id=invite.id).pack(),
        )
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_invite_actions(invite_id: int) -> InlineKeyboardMarkup:
    """Принять/отклонить приглашение."""
    b = InlineKeyboardBuilder()
    b.button(
        text="✅ Принять",
        callback_data=ClanMenu(action="invite_accept", invite_id=invite_id).pack(),
    )
    b.button(
        text="❌ Отклонить",
        callback_data=ClanMenu(action="invite_decline", invite_id=invite_id).pack(),
    )
    b.button(text="🔙 К приглашениям", callback_data=ClanMenu(action="invites").pack())
    b.adjust(2, 1)
    return b.as_markup()


def get_invite_cancel() -> InlineKeyboardMarkup:
    """Отмена ввода юзернейма для приглашения."""
    b = InlineKeyboardBuilder()
    b.button(text="❌ Отмена", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()


def get_outgoing_menu(invites: list) -> InlineKeyboardMarkup:
    """Исходящие приглашения клана."""
    b = InlineKeyboardBuilder()
    for inv in invites[:20]:
        b.button(
            text=f"⏳ К user_id={inv.to_user_id}",
            callback_data="noop",
        )
    b.button(text="🔙 Назад", callback_data=ClanMenu(action="menu").pack())
    b.adjust(1)
    return b.as_markup()
