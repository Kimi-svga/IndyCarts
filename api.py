"""IndyCarts API — REST для Visual Merge."""

import hashlib
import hmac
import json
import time
from pathlib import Path
from urllib.parse import parse_qsl

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import FileResponse
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import func, select

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
JWT_TTL = 60 * 60 * 24 * 7  # 7 дней

CACHE_DIR = Path("/tmp/indy_cards_cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════
# AUTH — проверка Telegram initData
# ═════════════════════════════════════════════

def verify_init_data(init_data: str, bot_token: str) -> dict:
    """Проверяет подпись Telegram initData."""
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
    """Принимает initData, возвращает JWT."""
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
# DEPS — текущий юзер из JWT
# ═════════════════════════════════════════════

async def get_current_user(
    authorization: str = Header(...),
) -> User:
    """Достаёт User из JWT."""
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
# ME — профиль игрока
# ═════════════════════════════════════════════

@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Профиль игрока."""
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
# CONFIG — константы для фронта
# ═════════════════════════════════════════════

@router.get("/config")
async def get_config():
    """Все константы для Visual Merge."""
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
# CARDS — коллекция и картинки
# ═════════════════════════════════════════════

@router.get("/cards")
async def get_cards(user: User = Depends(get_current_user)):
    """Коллекция игрока."""
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
    """Прокси картинки карты из Telegram (с кэшем)."""
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

    # Ленивый импорт — чтобы не было циклической зависимости
    from main import bot

    try:
        file = await bot.get_file(card.image_file_id)
        await bot.download_file(file.file_path, destination=cache_file)
    except Exception as e:
        raise HTTPException(500, f"Download failed: {e}")

    return FileResponse(
        cache_file,
        media_type="image/jpeg",
        headers={"Cache-Control": "public, max-age=86400"},
    )


# ═════════════════════════════════════════════
# HEALTH — проверка API
# ═════════════════════════════════════════════

@router.get("/health")
async def api_health():
    """Проверка API."""
    return {
        "status": "ok",
        "api": "v1",
        "service": "Visual Merge",
} 
