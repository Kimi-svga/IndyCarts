"""Сервис кланов: создание, вступление, вклад, уровни, бонусы."""

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.constants import (
    CLAN_LEVELS, CLAN_MAX_LEVEL, CLAN_MIN_LEVEL,
    CLAN_ROLE_LEVELS,
)
from core.logger import setup_logger
from db.models import (
    Clan, ClanInvite, ClanLog, ClanMember, User,
)

logger = setup_logger()


# ═════════════════════════════════════════════
# DATACLASSES
# ═════════════════════════════════════════════

@dataclass
class ClanResult:
    """Универсальный результат операции с кланом."""
    ok: bool
    reason: str = ""
    clan_id: int = 0
    data: dict | None = None


@dataclass
class ClanBonuses:
    """Бонусы клана для игрока."""
    drop_bonus: float = 0.0
    money_bonus: float = 0.0
    auction_discount: float = 0.0
    extra_attempts: int = 0
    max_members: int = 10
    level: int = 1


# ═════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════

def is_plus_active(user: User) -> bool:
    """Проверяет, что Indy+ активен прямо сейчас."""
    if user is None:
        return False
    if user.plus_tier != "indy_plus":
        return False
    if user.plus_expires_at is None:
        return False
    return user.plus_expires_at > datetime.utcnow()


def get_level_for_xp(xp: int) -> int:
    """Определяет уровень клана по XP."""
    level = CLAN_MIN_LEVEL
    for lvl in range(CLAN_MIN_LEVEL, CLAN_MAX_LEVEL + 1):
        if xp >= CLAN_LEVELS[lvl]["xp_required"]:
            level = lvl
        else:
            break
    return level


def get_xp_for_next_level(level: int) -> int:
    """Сколько XP нужно для следующего уровня. 0 — если максимум."""
    if level >= CLAN_MAX_LEVEL:
        return 0
    return CLAN_LEVELS[level + 1]["xp_required"]


def get_clan_bonuses(level: int) -> ClanBonuses:
    """Возвращает бонусы для уровня клана."""
    lvl = max(CLAN_MIN_LEVEL, min(level, CLAN_MAX_LEVEL))
    cfg = CLAN_LEVELS[lvl]
    return ClanBonuses(
        drop_bonus=cfg["drop_bonus"],
        money_bonus=cfg["money_bonus"],
        auction_discount=cfg["auction_discount"],
        extra_attempts=cfg["extra_attempts"],
        max_members=cfg["max_members"],
        level=lvl,
    )


def get_clan_role_level(role: str) -> int:
    """Числовой уровень роли в клане."""
    return CLAN_ROLE_LEVELS.get(role, 0)


def can_manage(actor_role: str, target_role: str) -> bool:
    """Может ли actor управлять target (kick/promote/demote)."""
    return get_clan_role_level(actor_role) > get_clan_role_level(target_role)


# ═════════════════════════════════════════════
# CREATE
# ═════════════════════════════════════════════

async def create_clan(
    session: AsyncSession,
    user: User,
    name: str,
    tag: str,
    description: str | None = None,
) -> ClanResult:
    """
    Создаёт клан.

    Indy+ — бесплатно.
    Обычные — 200 000 монет.
    """
    name = name.strip()
    tag = tag.strip().upper()

    # Валидация
    if not (3 <= len(name) <= 24):
        return ClanResult(ok=False, reason="Название: 3–24 символа")

    if not (2 <= len(tag) <= 4):
        return ClanResult(ok=False, reason="Тег: 2–4 символа")

    if not tag.isalpha():
        return ClanResult(ok=False, reason="Тег: только буквы")

    # Уже в клане?
    existing_member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == user.id)
    )).scalar_one_or_none()

    if existing_member is not None:
        return ClanResult(ok=False, reason="Ты уже в клане")

    # Название занято?
    name_taken = (await session.execute(
        select(Clan).where(Clan.name == name)
    )).scalar_one_or_none()
    if name_taken is not None:
        return ClanResult(ok=False, reason="Название занято")

    # Тег занят?
    tag_taken = (await session.execute(
        select(Clan).where(Clan.tag == tag)
    )).scalar_one_or_none()
    if tag_taken is not None:
        return ClanResult(ok=False, reason="Тег занят")

    # Оплата
    free_for_plus = settings.CLAN_CREATE_FREE_FOR_PLUS and is_plus_active(user)

    if not free_for_plus:
        price = settings.CLAN_CREATE_PRICE
        if user.balance < price:
            return ClanResult(
                ok=False,
                reason=f"Нужно {price:,} монет. У тебя {user.balance:,}.",
            )
        user.balance -= price

    # Создаём клан
    clan = Clan(
        name=name,
        tag=tag,
        description=(description or "").strip()[:200] or None,
        level=1,
        xp=0,
        treasury=0,
        owner_id=user.id,
        is_open=False,
        is_active=True,
    )
    session.add(clan)
    await session.flush()

    # Создатель — лидер
    member = ClanMember(
        clan_id=clan.id,
        user_id=user.id,
        role="leader",
        contribution=0,
    )
    session.add(member)

    # Лог
    session.add(ClanLog(
        clan_id=clan.id,
        user_id=user.id,
        action="create",
        amount=0,
        note=f"Клан {name} [{tag}]",
    ))

    await session.commit()

    logger.info(f"🏰 Клан создан: {name} [{tag}] by @{user.username}")

    return ClanResult(ok=True, clan_id=clan.id, data={"free": free_for_plus})


# ═════════════════════════════════════════════
# JOIN / LEAVE
# ═════════════════════════════════════════════

async def join_clan(
    session: AsyncSession,
    user: User,
    clan_id: int,
) -> ClanResult:
    """Вступает в клан (только если is_open)."""
    if user is None:
        return ClanResult(ok=False, reason="Игрок не найден")

    existing = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == user.id)
    )).scalar_one_or_none()
    if existing is not None:
        return ClanResult(ok=False, reason="Ты уже в клане")

    clan = (await session.execute(
        select(Clan).where(Clan.id == clan_id, Clan.is_active == True)
    )).scalar_one_or_none()

    if clan is None:
        return ClanResult(ok=False, reason="Клан не найден или закрыт")

    if not clan.is_open:
        return ClanResult(ok=False, reason="Клан закрыт. Нужно приглашение.")

    # Лимит
    max_members = get_clan_bonuses(clan.level).max_members
    count = (await session.execute(
        select(func.count(ClanMember.id)).where(ClanMember.clan_id == clan.id)
    )).scalar() or 0

    if count >= max_members:
        return ClanResult(ok=False, reason=f"Клан полон ({max_members})")

    session.add(ClanMember(
        clan_id=clan.id,
        user_id=user.id,
        role="member",
        contribution=0,
    ))

    session.add(ClanLog(
        clan_id=clan.id,
        user_id=user.id,
        action="join",
        amount=0,
    ))

    await session.commit()

    logger.info(f"📥 @{user.username} вступил в клан #{clan.id}")

    return ClanResult(ok=True, clan_id=clan.id)


async def leave_clan(
    session: AsyncSession,
    user: User,
) -> ClanResult:
    """Выходит из клана. Лидер не может выйти, пока есть участники."""
    member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == user.id)
    )).scalar_one_or_none()

    if member is None:
        return ClanResult(ok=False, reason="Ты не в клане")

    clan = await session.get(Clan, member.clan_id)
    if clan is None:
        return ClanResult(ok=False, reason="Клан не найден")

    if member.role == "leader":
        count = (await session.execute(
            select(func.count(ClanMember.id)).where(ClanMember.clan_id == clan.id)
        )).scalar() or 0

        if count > 1:
            return ClanResult(
                ok=False,
                reason="Ты лидер. Передай лидерство или распусти клан.",
            )

        # Последний в клане — распускаем
        clan.is_active = False
        session.add(ClanLog(
            clan_id=clan.id,
            user_id=user.id,
            action="disband",
        ))
        await session.delete(member)
        await session.commit()
        logger.info(f"💥 Клан #{clan.id} распущен (последний вышел)")
        return ClanResult(ok=True, clan_id=clan.id, data={"disbanded": True})

    clan_id = clan.id
    session.add(ClanLog(
        clan_id=clan_id,
        user_id=user.id,
        action="leave",
    ))
    await session.delete(member)
    await session.commit()

    logger.info(f"📤 @{user.username} вышел из клана #{clan_id}")

    return ClanResult(ok=True, clan_id=clan_id)


# ═════════════════════════════════════════════
# DEPOSIT (вклад)
# ═════════════════════════════════════════════

async def deposit(
    session: AsyncSession,
    user: User,
    amount: int,
) -> ClanResult:
    """Игрок вкладывает монеты в казну. Amount идёт и в treasury, и в xp."""
    if amount < 100:
        return ClanResult(ok=False, reason="Минимум 100 монет")

    member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == user.id)
    )).scalar_one_or_none()

    if member is None:
        return ClanResult(ok=False, reason="Ты не в клане")

    if user.balance < amount:
        return ClanResult(
            ok=False,
            reason=f"Нужно {amount:,}. У тебя {user.balance:,}.",
        )

    clan = await session.get(Clan, member.clan_id)
    if clan is None:
        return ClanResult(ok=False, reason="Клан не найден")

    user.balance -= amount
    clan.treasury += amount
    clan.xp += amount
    member.contribution += amount

    # Проверяем level up
    new_level = get_level_for_xp(clan.xp)
    leveled_up = False
    if new_level > clan.level and new_level <= CLAN_MAX_LEVEL:
        clan.level = new_level
        leveled_up = True
        session.add(ClanLog(
            clan_id=clan.id,
            user_id=None,
            action="level_up",
            amount=new_level,
            note=f"Уровень {new_level}",
        ))
        logger.info(f"🎉 Клан #{clan.id} → уровень {new_level}")

    session.add(ClanLog(
        clan_id=clan.id,
        user_id=user.id,
        action="deposit",
        amount=amount,
    ))

    await session.commit()

    return ClanResult(
        ok=True,
        clan_id=clan.id,
        data={
            "amount": amount,
            "leveled_up": leveled_up,
            "new_level": clan.level if leveled_up else None,
            "treasury": clan.treasury,
            "xp": clan.xp,
        },
    )


# ═════════════════════════════════════════════
# KICK / PROMOTE / DEMOTE
# ═════════════════════════════════════════════

async def kick_member(
    session: AsyncSession,
    actor: User,
    target_user_id: int,
) -> ClanResult:
    """Лидер/офицер исключает участника."""
    actor_member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == actor.id)
    )).scalar_one_or_none()
    if actor_member is None:
        return ClanResult(ok=False, reason="Ты не в клане")

    target_member = (await session.execute(
        select(ClanMember).where(
            ClanMember.user_id == target_user_id,
            ClanMember.clan_id == actor_member.clan_id,
        )
    )).scalar_one_or_none()

    if target_member is None:
        return ClanResult(ok=False, reason="Игрок не в твоём клане")

    if target_member.user_id == actor.id:
        return ClanResult(ok=False, reason="Нельзя исключить себя")

    if not can_manage(actor_member.role, target_member.role):
        return ClanResult(ok=False, reason="Недостаточно прав")

    clan_id = actor_member.clan_id
    session.add(ClanLog(
        clan_id=clan_id,
        user_id=target_user_id,
        action="kick",
        note=f"by @{actor.username}",
    ))
    await session.delete(target_member)
    await session.commit()

    logger.info(f"🚪 @{actor.username} кикнул user_id={target_user_id}")

    return ClanResult(ok=True, clan_id=clan_id)


async def set_role(
    session: AsyncSession,
    actor: User,
    target_user_id: int,
    new_role: str,
) -> ClanResult:
    """Меняет роль. Только лидер может повышать/понижать."""
    if new_role not in ("officer", "member"):
        return ClanResult(ok=False, reason="Только officer или member")

    actor_member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == actor.id)
    )).scalar_one_or_none()
    if actor_member is None or actor_member.role != "leader":
        return ClanResult(ok=False, reason="Только лидер меняет роли")

    target_member = (await session.execute(
        select(ClanMember).where(
            ClanMember.user_id == target_user_id,
            ClanMember.clan_id == actor_member.clan_id,
        )
    )).scalar_one_or_none()
    if target_member is None:
        return ClanResult(ok=False, reason="Игрок не в твоём клане")

    if target_member.user_id == actor.id:
        return ClanResult(ok=False, reason="Нельзя менять свою роль")

    target_member.role = new_role

    session.add(ClanLog(
        clan_id=actor_member.clan_id,
        user_id=target_user_id,
        action="promote" if new_role == "officer" else "demote",
        note=f"by @{actor.username}",
    ))

    await session.commit()

    return ClanResult(ok=True, clan_id=actor_member.clan_id)


# ═════════════════════════════════════════════
# GETTERS
# ═════════════════════════════════════════════

async def get_user_clan(
    session: AsyncSession,
    user_id: int,
) -> tuple[Clan | None, ClanMember | None]:
    """Возвращает (Clan, ClanMember) для игрока."""
    member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == user_id)
    )).scalar_one_or_none()

    if member is None:
        return None, None

    clan = await session.get(Clan, member.clan_id)
    return clan, member


async def get_clan_members(
    session: AsyncSession,
    clan_id: int,
    limit: int = 100,
) -> list[tuple[ClanMember, User]]:
    """Возвращает список (ClanMember, User) для клана."""
    rows = (await session.execute(
        select(ClanMember, User)
        .join(User, ClanMember.user_id == User.id)
        .where(ClanMember.clan_id == clan_id)
        .limit(limit)
    )).all()

    # Сортировка по уровню роли, затем по вкладу
    rows = list(rows)
    rows.sort(
        key=lambda r: (-get_clan_role_level(r[0].role), -r[0].contribution),
    )
    return rows


async def get_clan_rating(
    session: AsyncSession,
    clan_id: int,
) -> int:
    """
    Рейтинг клана = xp + treasury + Σ(pvp_rating членов).
    """
    clan = await session.get(Clan, clan_id)
    if clan is None:
        return 0

    pvp_sum = (await session.execute(
        select(func.coalesce(func.sum(User.pvp_rating), 0))
        .join(ClanMember, ClanMember.user_id == User.id)
        .where(ClanMember.clan_id == clan_id)
    )).scalar() or 0

    return int(clan.xp + clan.treasury + pvp_sum)


async def get_top_clans(
    session: AsyncSession,
    limit: int = 10,
) -> list[tuple[Clan, int]]:
    """
    Топ кланов по рейтингу.
    Возвращает [(Clan, rating)].
    """
    pvp_subq = (
        select(
            ClanMember.clan_id,
            func.coalesce(func.sum(User.pvp_rating), 0).label("pvp_sum"),
        )
        .join(User, ClanMember.user_id == User.id)
        .group_by(ClanMember.clan_id)
        .subquery()
    )

    rating_expr = (
        Clan.xp + Clan.treasury + func.coalesce(pvp_subq.c.pvp_sum, 0)
    ).label("rating")

    rows = (await session.execute(
        select(Clan, rating_expr)
        .outerjoin(pvp_subq, pvp_subq.c.clan_id == Clan.id)
        .where(Clan.is_active == True)
        .order_by(rating_expr.desc())
        .limit(limit)
    )).all()

    return [(row[0], int(row[1])) for row in rows]


async def get_clan_member_count(
    session: AsyncSession,
    clan_id: int,
) -> int:
    """Сколько людей в клане."""
    return (await session.execute(
        select(func.count(ClanMember.id)).where(ClanMember.clan_id == clan_id)
    )).scalar() or 0


async def get_clan_member_by_user(
    session: AsyncSession,
    clan_id: int,
    user_id: int,
) -> ClanMember | None:
    """Возвращает ClanMember конкретного игрока в конкретном клане."""
    return (await session.execute(
        select(ClanMember).where(
            ClanMember.clan_id == clan_id,
            ClanMember.user_id == user_id,
        )
    )).scalar_one_or_none()


async def find_clan_by_name(
    session: AsyncSession,
    name: str,
) -> Clan | None:
    """Ищет клан по имени (точное совпадение)."""
    return (await session.execute(
        select(Clan).where(Clan.name == name, Clan.is_active == True)
    )).scalar_one_or_none()


async def find_clan_by_tag(
    session: AsyncSession,
    tag: str,
) -> Clan | None:
    """Ищет клан по тегу."""
    return (await session.execute(
        select(Clan).where(Clan.tag == tag.upper(), Clan.is_active == True)
    )).scalar_one_or_none()


async def search_clans(
    session: AsyncSession,
    query: str,
    limit: int = 20,
) -> list[Clan]:
    """Поиск кланов по подстроке в name/tag."""
    q = f"%{query.strip()}%"
    return (await session.execute(
        select(Clan)
        .where(
            Clan.is_active == True,
            (Clan.name.ilike(q)) | (Clan.tag.ilike(q)),
        )
        .limit(limit)
    )).scalars().all()


# ═════════════════════════════════════════════
# INVITES
# ═════════════════════════════════════════════

async def create_invite(
    session: AsyncSession,
    actor: User,
    target_user_id: int,
) -> ClanResult:
    """Лидер/офицер приглашает игрока в свой клан."""
    actor_member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == actor.id)
    )).scalar_one_or_none()

    if actor_member is None:
        return ClanResult(ok=False, reason="Ты не в клане")

    if get_clan_role_level(actor_member.role) < CLAN_ROLE_LEVELS["officer"]:
        return ClanResult(ok=False, reason="Только лидер и офицер приглашают")

    if actor.id == target_user_id:
        return ClanResult(ok=False, reason="Нельзя пригласить себя")

    target_member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == target_user_id)
    )).scalar_one_or_none()

    if target_member is not None:
        return ClanResult(ok=False, reason="Игрок уже в клане")

    # Уже есть pending?
    existing = (await session.execute(
        select(ClanInvite).where(
            ClanInvite.clan_id == actor_member.clan_id,
            ClanInvite.to_user_id == target_user_id,
            ClanInvite.status == "pending",
        )
    )).scalar_one_or_none()

    if existing is not None:
        return ClanResult(ok=False, reason="Приглашение уже отправлено")

    # Лимит pending
    pending_count = (await session.execute(
        select(func.count(ClanInvite.id)).where(
            ClanInvite.clan_id == actor_member.clan_id,
            ClanInvite.status == "pending",
        )
    )).scalar() or 0

    if pending_count >= 20:
        return ClanResult(ok=False, reason="Слишком много активных приглашений")

    invite = ClanInvite(
        clan_id=actor_member.clan_id,
        from_user_id=actor.id,
        to_user_id=target_user_id,
        status="pending",
        expires_at=datetime.utcnow() + timedelta(
            hours=settings.CLAN_INVITE_TIMEOUT_HOURS
        ),
    )
    session.add(invite)
    await session.commit()

    logger.info(f"📨 @{actor.username} пригласил user_id={target_user_id}")

    return ClanResult(
        ok=True,
        clan_id=actor_member.clan_id,
        data={"invite_id": invite.id},
    )


async def accept_invite(
    session: AsyncSession,
    user: User,
    invite_id: int,
) -> ClanResult:
    """Принять приглашение в клан."""
    invite = (await session.execute(
        select(ClanInvite).where(
            ClanInvite.id == invite_id,
            ClanInvite.to_user_id == user.id,
            ClanInvite.status == "pending",
        )
    )).scalar_one_or_none()

    if invite is None:
        return ClanResult(ok=False, reason="Приглашение не найдено")

    if invite.expires_at < datetime.utcnow():
        invite.status = "expired"
        invite.resolved_at = datetime.utcnow()
        await session.commit()
        return ClanResult(ok=False, reason="Приглашение истекло")

    # Уже в клане?
    existing_member = (await session.execute(
        select(ClanMember).where(ClanMember.user_id == user.id)
    )).scalar_one_or_none()

    if existing_member is not None:
        invite.status = "declined"
        invite.resolved_at = datetime.utcnow()
        await session.commit()
        return ClanResult(ok=False, reason="Ты уже в клане")

    clan = await session.get(Clan, invite.clan_id)
    if clan is None or not clan.is_active:
        return ClanResult(ok=False, reason="Клан недоступен")

    max_members = get_clan_bonuses(clan.level).max_members
    count = (await session.execute(
        select(func.count(ClanMember.id)).where(ClanMember.clan_id == clan.id)
    )).scalar() or 0

    if count >= max_members:
        return ClanResult(ok=False, reason=f"Клан полон ({max_members})")

    session.add(ClanMember(
        clan_id=clan.id,
        user_id=user.id,
        role="member",
        contribution=0,
    ))

    session.add(ClanLog(
        clan_id=clan.id,
        user_id=user.id,
        action="join",
        note="по приглашению",
    ))

    invite.status = "accepted"
    invite.resolved_at = datetime.utcnow()

    await session.commit()

    logger.info(f"✅ @{user.username} принял приглашение в клан #{clan.id}")

    return ClanResult(ok=True, clan_id=clan.id)


async def decline_invite(
    session: AsyncSession,
    user: User,
    invite_id: int,
) -> ClanResult:
    """Отклонить приглашение."""
    invite = (await session.execute(
        select(ClanInvite).where(
            ClanInvite.id == invite_id,
            ClanInvite.to_user_id == user.id,
            ClanInvite.status == "pending",
        )
    )).scalar_one_or_none()

    if invite is None:
        return ClanResult(ok=False, reason="Приглашение не найдено")

    invite.status = "declined"
    invite.resolved_at = datetime.utcnow()
    await session.commit()

    return ClanResult(ok=True, clan_id=invite.clan_id)


async def get_pending_invites(
    session: AsyncSession,
    user_id: int,
) -> list[tuple[ClanInvite, Clan, User]]:
    """Все pending приглашения игроку."""
    rows = (await session.execute(
        select(ClanInvite, Clan, User)
        .join(Clan, ClanInvite.clan_id == Clan.id)
        .join(User, ClanInvite.from_user_id == User.id)
        .where(
            ClanInvite.to_user_id == user_id,
            ClanInvite.status == "pending",
            ClanInvite.expires_at > datetime.utcnow(),
        )
        .order_by(ClanInvite.created_at.desc())
        .limit(20)
    )).all()
    return list(rows)


async def get_clan_pending_invites(
    session: AsyncSession,
    clan_id: int,
) -> list[ClanInvite]:
    """Все pending приглашения клана (исходящие)."""
    return (await session.execute(
        select(ClanInvite)
        .where(
            ClanInvite.clan_id == clan_id,
            ClanInvite.status == "pending",
            ClanInvite.expires_at > datetime.utcnow(),
        )
        .order_by(ClanInvite.created_at.desc())
        .limit(50)
    )).scalars().all()


# ═════════════════════════════════════════════
# LOG
# ═════════════════════════════════════════════

async def get_clan_log(
    session: AsyncSession,
    clan_id: int,
    limit: int = 20,
) -> list[tuple[ClanLog, User | None]]:
    """Последние события клана."""
    rows = (await session.execute(
        select(ClanLog, User)
        .outerjoin(User, ClanLog.user_id == User.id)
        .where(ClanLog.clan_id == clan_id)
        .order_by(ClanLog.created_at.desc())
        .limit(limit)
    )).all()
    return list(rows) 
