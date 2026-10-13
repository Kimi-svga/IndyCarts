"""IndyCarts API — REST для Visual Merge."""

import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import func, select

from bot_instance import bot
from core.config import settings
from core.constants import (
    BAN_LEVELS, BAN_NAMES, BASE_PRICES, CLAN_LEVELS,
    DROP_CHANCES, LOAN_RATES, LOAN_TERMS, MERGE_RULES,
    PVP_TITLES, RARITIES, RARITY_EMOJI, RARITY_NAMES,
    ROLE_EMOJI, ROLE_LEVELS, ROLE_NAMES,
    TICKET_CATEGORIES, TRUST_DELTA, TRUST_RANKS,
)
from db.models import Card, User, UserCard
from db.session import AsyncSessionLocal

router = APIRouter(prefix="/api", tags=["api"])

JWT_SECRET = settings.WEBHOOK_SECRET
JWT_ALGO = "HS256"
JWT_TTL = 60 * 60 * 24 * 7

CACHE_DIR = Path("/tmp/indy_cards_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════
# AUTH
# ═════════════════════════════════════════════

def verify_init_data(init_data: str, bot_token: str) -> dict:
    parsed = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise ValueError("No hash in initData")

    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )
    secret_key = hmac.new(
        b"WebAppData", bot_token.encode(), hashlib.sha256
    ).digest()
    expected_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_hash, received_hash):
        raise ValueError("Invalid signature")

    auth_date = int(parsed.get("auth_date", 0))
    if time.time() - auth_date > 86400:
        raise ValueError("initData expired")

    user_json = parsed.get("user")
    if not user_json:
        raise ValueError("No user in initData")

    return json.loads(user_json)


class AuthRequest(BaseModel):
    init_data: str


class AuthResponse(BaseModel):
    token: str
    telegram_id: int
    username: str


@router.post("/auth/telegram", response_model=AuthResponse)
async def auth_telegram(payload: AuthRequest) -> AuthResponse:
    try:
        tg_user = verify_init_data(payload.init_data, settings.BOT_TOKEN)
    except ValueError as e:
        raise HTTPException(401, str(e))

    token = jwt.encode(
        {
            "sub": str(tg_user["id"]),
            "username": tg_user.get("username", ""),
            "exp": int(time.time()) + JWT_TTL,
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )

    return AuthResponse(
        token=token,
        telegram_id=tg_user["id"],
        username=tg_user.get("username", ""),
    )


# ═════════════════════════════════════════════
# DEPS
# ═════════════════════════════════════════════

async def get_current_user(
    authorization: str = Header(...),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid auth header")

    token = authorization[7:]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
        telegram_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(401, "Invalid token")

    async with AsyncSessionLocal() as session:
        user = (await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )).scalar_one_or_none()

    if user is None:
        raise HTTPException(404, "User not found")

    return user


# ═════════════════════════════════════════════
# ME
# ═════════════════════════════════════════════

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        cards_count = (await session.execute(
            select(func.count(UserCard.id)).where(UserCard.user_id == user.id)
        )).scalar() or 0

        collection_value = (await session.execute(
            select(func.sum(Card.current_price))
            .join(UserCard, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )).scalar() or 0

    return {
        "telegram_id": user.telegram_id,
        "username": user.username,
        "balance": user.balance,
        "cards_count": cards_count,
        "collection_value": int(collection_value),
        "pvp_rating": user.pvp_rating,
        "pvp_wins": user.pvp_wins,
        "pvp_losses": user.pvp_losses,
        "daily_streak": user.daily_streak,
        "trust_score": user.trust_score,
        "daily_attempts": user.daily_attempts,
        "plus_tier": user.plus_tier,
        "plus_expires_at": user.plus_expires_at.isoformat() if user.plus_expires_at else None,
        "ban_level": user.ban_level,
        "created_at": user.created_at.isoformat(),
    }


# ═════════════════════════════════════════════
# CONFIG
# ═════════════════════════════════════════════

@router.get("/config")
async def get_config():
    return {
        "rarities": RARITIES,
        "rarityNames": RARITY_NAMES,
        "rarityEmoji": RARITY_EMOJI,
        "basePrices": BASE_PRICES,
        "dropChances": DROP_CHANCES,
        "clanLevels": CLAN_LEVELS,
        "trustRanks": TRUST_RANKS,
        "trustDelta": TRUST_DELTA,
        "pvpTitles": PVP_TITLES,
        "loanRates": LOAN_RATES,
        "loanTerms": LOAN_TERMS,
        "roleLevels": ROLE_LEVELS,
        "roleEmoji": ROLE_EMOJI,
        "roleNames": ROLE_NAMES,
        "banLevels": BAN_LEVELS,
        "banNames": BAN_NAMES,
        "ticketCategories": TICKET_CATEGORIES,
        "mergeRules": MERGE_RULES,
    }


# ═════════════════════════════════════════════
# CARDS
# ═════════════════════════════════════════════

@router.get("/cards")
async def get_cards(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        rows = (await session.execute(
            select(
                Card,
                func.count(UserCard.id).label("count"),
            )
            .join(UserCard, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
            .group_by(Card.id)
            .order_by(Card.rarity, Card.name)
        )).all()

    return [
        {
            "id": card.id,
            "name": card.name,
            "rarity": card.rarity,
            "team": card.team,
            "year": card.year,
            "price": card.current_price,
            "image_url": f"/api/cards/{card.id}/image" if card.image_file_id else None,
            "count": count,
            "max_supply": card.max_supply,
            "issued": card.issued,
        }
        for card, count in rows
    ]


@router.get("/cards/{card_id}/image")
async def get_card_image(card_id: int):
    cache_file = CACHE_DIR / f"{card_id}.jpg"
    if cache_file.exists():
        return FileResponse(
            cache_file,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    async with AsyncSessionLocal() as session:
        card = await session.get(Card, card_id)

    if card is None:
        raise HTTPException(404, "Card not found")
    if not card.image_file_id:
        raise HTTPException(404, "Card has no image")

    try:
        file = await bot.get_file(card.image_file_id)
        await bot.download_file(file.file_path, destination=cache_file)
    except Exception as e:
        raise HTTPException(500, f"Download failed: {type(e).__name__}: {e}")

    return FileResponse(
        cache_file,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ═════════════════════════════════════════════
# CARD ACTIONS
# ═════════════════════════════════════════════

class SellCardRequest(BaseModel):
    card_id: int


class GiftCardRequest(BaseModel):
    card_id: int
    username: str


@router.post("/card/sell")
async def sell_card(
    payload: SellCardRequest,
    user: User = Depends(get_current_user),
):
    async with AsyncSessionLocal() as session:
        user_card = (await session.execute(
            select(UserCard)
            .where(
                UserCard.user_id == user.id,
                UserCard.card_id == payload.card_id,
                UserCard.is_locked == False,
            )
            .limit(1)
        )).scalar_one_or_none()

        if user_card is None:
            raise HTTPException(404, "Карта не найдена")

        card = await session.get(Card, payload.card_id)
        if card is None:
            raise HTTPException(404, "Карта не найдена")

        price = int(card.current_price * 0.9)

        await session.delete(user_card)

        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "Юзер не найден")
        user_row.balance += price

        await session.commit()

        return {
            "ok": True,
            "card_name": card.name,
            "price": price,
            "new_balance": user_row.balance,
        }


@router.post("/card/gift")
async def gift_card(
    payload: GiftCardRequest,
    user: User = Depends(get_current_user),
):
    username = payload.username.lstrip("@").lower()

    if username == user.username_normalized:
        raise HTTPException(400, "Нельзя подарить себе")

    async with AsyncSessionLocal() as session:
        receiver = (await session.execute(
            select(User).where(User.username_normalized == username)
        )).scalar_one_or_none()

        if receiver is None:
            raise HTTPException(404, f"@{username} не найден")

        user_card = (await session.execute(
            select(UserCard)
            .where(
                UserCard.user_id == user.id,
                UserCard.card_id == payload.card_id,
                UserCard.is_locked == False,
            )
            .limit(1)
        )).scalar_one_or_none()

        if user_card is None:
            raise HTTPException(404, "Карта не найдена")

        card = await session.get(Card, payload.card_id)
        if card is None:
            raise HTTPException(404, "Карта не найдена")

        user_card.user_id = receiver.id
        await session.commit()

        return {
            "ok": True,
            "card_name": card.name,
            "receiver": receiver.username,
        }


# ═════════════════════════════════════════════
# ADMIN COMMAND
# ═════════════════════════════════════════════

class CommandRequest(BaseModel):
    command: str
    args: list[str] = []
    flags: dict[str, str | bool] = {}


@router.post("/admin/command")
async def admin_command(
    payload: CommandRequest,
    user: User = Depends(get_current_user),
):
    if (
        user.telegram_id not in settings.OWNER_IDS
        and user.telegram_id not in settings.ADMIN_IDS
    ):
        raise HTTPException(403, "Insufficient permissions")

    async with AsyncSessionLocal() as session:
        result = await _dispatch_command(
            session, payload.command, payload.args, payload.flags
        )

    return {"result": result}


async def _dispatch_command(
    session,
    command: str,
    args: list[str],
    flags: dict[str, str | bool],
):
    from db.models import User as UserModel, UserCard, Card

    if command == "user.info":
        username = args[0].lstrip("@").lower()
        u = (await session.execute(
            select(UserModel).where(UserModel.username_normalized == username)
        )).scalar_one_or_none()

        if u is None:
            raise HTTPException(404, f"@{username} not found")

        return {
            "id": u.id,
            "telegramId": u.telegram_id,
            "username": u.username,
            "balance": u.balance,
            "pvpRating": u.pvp_rating,
            "pvpWins": u.pvp_wins,
            "pvpLosses": u.pvp_losses,
            "dailyStreak": u.daily_streak,
            "trustScore": u.trust_score,
            "plusTier": u.plus_tier,
            "plusExpiresAt": u.plus_expires_at.isoformat() if u.plus_expires_at else None,
            "banLevel": u.ban_level,
        }

    if command == "user.list":
        stmt = select(UserModel).order_by(UserModel.balance.desc())
        if flags.get("plus"):
            stmt = stmt.where(UserModel.plus_tier == "indy_plus")
        limit = int(flags.get("limit", 20)) if isinstance(flags.get("limit"), str) else 20
        stmt = stmt.limit(limit)
        users = (await session.execute(stmt)).scalars().all()

        return [
            {
                "id": u.id,
                "telegramId": u.telegram_id,
                "username": u.username,
                "balance": u.balance,
                "pvpRating": u.pvp_rating,
                "pvpWins": u.pvp_wins,
                "pvpLosses": u.pvp_losses,
                "dailyStreak": u.daily_streak,
                "trustScore": u.trust_score,
                "plusTier": u.plus_tier,
                "plusExpiresAt": u.plus_expires_at.isoformat() if u.plus_expires_at else None,
                "banLevel": u.ban_level,
            }
            for u in users
        ]

    if command == "user.search":
        query = str(flags.get("query", "")).lower()
        users = (await session.execute(
            select(UserModel)
            .where(UserModel.username_normalized.ilike(f"%{query}%"))
            .limit(20)
        )).scalars().all()

        return [
            {
                "id": u.id,
                "telegramId": u.telegram_id,
                "username": u.username,
                "balance": u.balance,
                "pvpRating": u.pvp_rating,
                "pvpWins": u.pvp_wins,
                "pvpLosses": u.pvp_losses,
                "dailyStreak": u.daily_streak,
                "trustScore": u.trust_score,
                "plusTier": u.plus_tier,
                "plusExpiresAt": None,
                "banLevel": u.ban_level,
            }
            for u in users
        ]

    if command == "user.ban":
        user_id = int(args[0])
        duration = str(flags.get("duration", "30d"))
        reason = str(flags.get("reason", "no reason"))

        target = await session.get(UserModel, user_id)
        if target is None:
            raise HTTPException(404, "user not found")

        target.ban_level = "ban"
        if duration == "perm":
            target.ban_expires_at = None
        else:
            days = 30
            if duration.endswith("d"):
                try:
                    days = int(duration[:-1])
                except ValueError:
                    days = 30
            elif duration.endswith("h"):
                try:
                    days = max(1, int(duration[:-1]) // 24)
                except ValueError:
                    days = 30
            target.ban_expires_at = datetime.utcnow() + timedelta(days=days)

        await session.commit()
        return {
            "ok": True,
            "username": target.username,
            "duration": duration,
            "reason": reason,
        }

    if command == "user.unban":
        user_id = int(args[0])
        target = await session.get(UserModel, user_id)
        if target is None:
            raise HTTPException(404, "user not found")
        target.ban_level = "none"
        target.ban_expires_at = None
        await session.commit()
        return {"ok": True, "username": target.username}

    if command == "user.set-balance":
        user_id = int(args[0])
        amount = int(flags.get("amount", 0))
        target = await session.get(UserModel, user_id)
        if target is None:
            raise HTTPException(404, "user not found")
        old = target.balance
        target.balance = amount
        await session.commit()
        return {
            "ok": True,
            "username": target.username,
            "old": old,
            "new": amount,
        }

    if command == "card.list":
        stmt = select(Card).where(Card.is_active == True)
        if flags.get("rarity"):
            stmt = stmt.where(Card.rarity == flags["rarity"])
        limit = int(flags.get("limit", 20)) if isinstance(flags.get("limit"), str) else 20
        stmt = stmt.limit(limit)
        cards = (await session.execute(stmt)).scalars().all()

        return [
            {
                "id": c.id,
                "name": c.name,
                "rarity": c.rarity,
                "team": c.team,
                "year": c.year,
                "price": c.current_price,
                "imageUrl": f"/api/cards/{c.id}/image" if c.image_file_id else None,
                "count": 0,
                "maxSupply": c.max_supply,
                "issued": c.issued,
            }
            for c in cards
        ]

    if command == "card.info":
        card_id = int(flags.get("id", 0))
        c = await session.get(Card, card_id)
        if c is None:
            raise HTTPException(404, "card not found")

        return {
            "id": c.id,
            "name": c.name,
            "rarity": c.rarity,
            "team": c.team,
            "year": c.year,
            "price": c.current_price,
            "imageUrl": f"/api/cards/{c.id}/image" if c.image_file_id else None,
            "count": 0,
            "maxSupply": c.max_supply,
            "issued": c.issued,
        }

    if command == "card.set-price":
        card_id = int(flags.get("id", 0))
        price = int(flags.get("price", 0))
        c = await session.get(Card, card_id)
        if c is None:
            raise HTTPException(404, "card not found")
        old = c.current_price
        c.current_price = price
        await session.commit()
        return {"ok": True, "name": c.name, "old": old, "new": price}

    if command == "card.give":
        user_id = int(args[0])
        card_id = int(flags.get("id", 0))
        u = await session.get(UserModel, user_id)
        if u is None:
            raise HTTPException(404, "user not found")
        c = await session.get(Card, card_id)
        if c is None:
            raise HTTPException(404, "card not found")

        session.add(UserCard(user_id=u.id, card_id=c.id, acquired_price=0))
        await session.commit()
        return {"ok": True, "username": u.username, "card": c.name}

    raise HTTPException(400, f"unknown command: {command}")


# ═════════════════════════════════════════════
# HEALTH
# ═════════════════════════════════════════════

@router.get("/health")
async def api_health():
    return {
        "status": "ok",
        "api": "v1",
        "service": "Visual Merge",
    }
