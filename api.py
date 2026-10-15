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
from services.notifications import (
    clear_user_notifications,
    get_unread_count,
    get_user_notifications,
    mark_read,
)

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
# DROP
# ═════════════════════════════════════════════

@router.post("/drop")
async def drop_card(user: User = Depends(get_current_user)):
    from services.drop import Drop
    from services.clan import get_clan_bonuses, get_user_clan

    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        if user_row.daily_attempts <= 0:
            raise HTTPException(400, "Попытки закончились")

        clan, _ = await get_user_clan(session, user_row.id)
        bonuses = get_clan_bonuses(clan.level) if clan else None
        drop_bonus = bonuses.drop_bonus if bonuses else 0.0

        card, is_iw = await Drop.drop_card_with_bonus(session, drop_bonus)

        if card is None:
            raise HTTPException(500, "Нет карт в базе")

        serial = None
        if card.max_supply is not None:
            card.issued += 1
            serial = card.issued

        session.add(UserCard(
            user_id=user_row.id,
            card_id=card.id,
            is_iw=is_iw,
            acquired_price=card.current_price,
            serial_number=serial,
        ))
        user_row.daily_attempts -= 1

        bonus_money = 0
        if bonuses and bonuses.money_bonus > 0:
            bonus_money = int(10 * (1 + bonuses.money_bonus))
            user_row.balance += bonus_money

        await session.commit()

        return {
            "ok": True,
            "card": {
                "id": card.id,
                "name": card.name,
                "rarity": card.rarity,
                "team": card.team,
                "year": card.year,
                "price": card.current_price,
                "image_url": f"/api/cards/{card.id}/image" if card.image_file_id else None,
                "max_supply": card.max_supply,
                "issued": card.issued,
            },
            "is_iw": is_iw,
            "serial": serial,
            "bonus_money": bonus_money,
            "attempts_left": user_row.daily_attempts,
            "new_balance": user_row.balance,
        }


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
# MARKET
# ═════════════════════════════════════════════

class MarketBuyRequest(BaseModel):
    card_id: int


@router.get("/market/list")
async def market_list(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        cards = (await session.execute(
            select(Card)
            .where(Card.is_active == True)
            .order_by(Card.current_price.desc())
            .limit(30)
        )).scalars().all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "rarity": c.rarity,
            "team": c.team,
            "year": c.year,
            "price": c.current_price,
            "base_price": c.base_price,
            "image_url": f"/api/cards/{c.id}/image" if c.image_file_id else None,
            "max_supply": c.max_supply,
            "issued": c.issued,
        }
        for c in cards
    ]


@router.post("/market/buy")
async def market_buy(
    payload: MarketBuyRequest,
    user: User = Depends(get_current_user),
):
    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        card = await session.get(Card, payload.card_id)
        if card is None or not card.is_active:
            raise HTTPException(404, "Карта не найдена")

        price = card.current_price

        if user_row.balance < price:
            raise HTTPException(400, f"Нужно {price:,} монет")

        if card.max_supply is not None and card.issued >= card.max_supply:
            raise HTTPException(400, "Тираж исчерпан")

        serial = None
        if card.max_supply is not None:
            card.issued += 1
            serial = card.issued

        user_row.balance -= price

        session.add(UserCard(
            user_id=user_row.id,
            card_id=card.id,
            acquired_price=price,
            serial_number=serial,
        ))

        await session.commit()

        return {
            "ok": True,
            "card_name": card.name,
            "price": price,
            "new_balance": user_row.balance,
            "serial": serial,
        }


# ═════════════════════════════════════════════
# BANK
# ═════════════════════════════════════════════

class LoanRequest(BaseModel):
    amount: int


class RepayRequest(BaseModel):
    amount: int


@router.get("/bank/info")
async def bank_info(user: User = Depends(get_current_user)):
    from db.models import Loan
    from services.bank import calculate_max_loan, get_trust_rank

    async with AsyncSessionLocal() as session:
        loan = (await session.execute(
            select(Loan).where(
                Loan.user_id == user.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

    max_loan = calculate_max_loan(user)
    trust_rank = get_trust_rank(user.trust_score)

    active_loan = None
    if loan is not None:
        days_left = (loan.due_at - datetime.utcnow()).days
        remaining = loan.total_due - loan.paid
        active_loan = {
            "id": loan.id,
            "principal": loan.principal,
            "rate": float(loan.rate),
            "total_due": loan.total_due,
            "paid": loan.paid,
            "remaining": remaining,
            "due_at": loan.due_at.isoformat(),
            "days_left": days_left,
            "status": loan.status,
        }

    return {
        "balance": user.balance,
        "trust_score": user.trust_score,
        "trust_rank": trust_rank,
        "max_loan": max_loan,
        "active_loan": active_loan,
    }


@router.post("/bank/loan")
async def bank_loan(
    payload: LoanRequest,
    user: User = Depends(get_current_user),
):
    from db.models import Loan
    from services.bank import (
        calculate_max_loan,
        calculate_total_due,
        get_loan_rate,
        get_loan_term,
    )

    if payload.amount < 1000:
        raise HTTPException(400, "Минимум 1 000")

    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        existing = (await session.execute(
            select(Loan).where(
                Loan.user_id == user_row.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        if existing is not None:
            raise HTTPException(400, "Уже есть активный кредит")

        max_loan = calculate_max_loan(user_row)
        if payload.amount > max_loan:
            raise HTTPException(400, f"Максимум {max_loan:,}")

        rate = get_loan_rate(payload.amount)
        term_days = get_loan_term(payload.amount)
        total_due = calculate_total_due(payload.amount)
        due_at = datetime.utcnow() + timedelta(days=term_days)

        user_row.balance += payload.amount
        user_row.loan_amount = total_due
        user_row.loan_due_at = due_at
        user_row.loans_count += 1
        user_row.total_borrowed += payload.amount

        session.add(Loan(
            user_id=user_row.id,
            principal=payload.amount,
            rate=rate,
            total_due=total_due,
            due_at=due_at,
            status="active",
        ))

        await session.commit()

        return {
            "ok": True,
            "amount": payload.amount,
            "rate": float(rate),
            "total_due": total_due,
            "due_at": due_at.isoformat(),
            "new_balance": user_row.balance,
        }


@router.post("/bank/repay")
async def bank_repay(
    payload: RepayRequest,
    user: User = Depends(get_current_user),
):
    from db.models import Loan, LoanPayment
    from services.bank import apply_trust, early_repay_discount, is_early_repay

    if payload.amount <= 0:
        raise HTTPException(400, "Сумма > 0")

    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        loan = (await session.execute(
            select(Loan).where(
                Loan.user_id == user_row.id,
                Loan.status.in_(["active", "overdue"]),
            )
        )).scalar_one_or_none()

        if loan is None:
            raise HTTPException(404, "Нет активного кредита")

        remaining = loan.total_due - loan.paid

        discount = 0
        if is_early_repay(loan):
            discount = early_repay_discount(remaining)
            remaining -= discount

        amount = min(payload.amount, remaining)
        closes_loan = amount >= remaining

        if user_row.balance < amount:
            raise HTTPException(400, f"Нужно {amount:,}")

        user_row.balance -= amount
        loan.paid += amount

        session.add(LoanPayment(loan_id=loan.id, amount=amount))

        trust_msg = ""
        if closes_loan:
            if is_early_repay(loan):
                delta = apply_trust(user_row, "early_repay")
                trust_msg = f"Досрочно! Trust +{delta}"
            else:
                delta = apply_trust(user_row, "on_time")
                trust_msg = f"В срок! Trust +{delta}"

            loan.status = "repaid"
            loan.repaid_at = datetime.utcnow()
            user_row.loan_amount = 0
            user_row.loan_due_at = None
            user_row.loans_repaid += 1

        await session.commit()

        return {
            "ok": True,
            "amount": amount,
            "discount": discount,
            "closes_loan": closes_loan,
            "remaining": max(0, remaining - amount),
            "new_balance": user_row.balance,
            "trust_msg": trust_msg,
        }


# ═════════════════════════════════════════════
# SHOP
# ═════════════════════════════════════════════

class ShopAttemptsRequest(BaseModel):
    attempts: int


@router.get("/shop/info")
async def shop_info(user: User = Depends(get_current_user)):
    return {
        "coin_per_attempt": settings.SHOP_COIN_PER_ATTEMPT,
        "max_attempts_per_day": settings.MAX_ATTEMPTS_PER_DAY,
        "shop_attempts_today": user.shop_attempts_today,
        "balance": user.balance,
        "plus_price_coins": settings.PLUS_PRICE_COINS,
        "plus_price_stars": settings.PLUS_PRICE_STARS,
        "plus_duration_days": settings.PLUS_DURATION_DAYS,
    }


@router.post("/shop/attempts")
async def shop_buy_attempts(
    payload: ShopAttemptsRequest,
    user: User = Depends(get_current_user),
):
    from datetime import date

    if payload.attempts <= 0:
        raise HTTPException(400, "Количество > 0")

    cost = payload.attempts * settings.SHOP_COIN_PER_ATTEMPT

    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        today = date.today()
        if user_row.last_shop_date != today:
            user_row.shop_attempts_today = 0
            user_row.last_shop_date = today

        if user_row.shop_attempts_today + payload.attempts > settings.MAX_ATTEMPTS_PER_DAY:
            raise HTTPException(400, f"Лимит {settings.MAX_ATTEMPTS_PER_DAY} попыток в день")

        if user_row.balance < cost:
            raise HTTPException(400, f"Нужно {cost:,} монет")

        user_row.balance -= cost
        user_row.daily_attempts += payload.attempts
        user_row.shop_attempts_today += payload.attempts

        await session.commit()

        return {
            "ok": True,
            "attempts": payload.attempts,
            "cost": cost,
            "new_balance": user_row.balance,
            "total_attempts": user_row.daily_attempts,
        }


# ═════════════════════════════════════════════
# PVP
# ═════════════════════════════════════════════

class PvpDuelRequest(BaseModel):
    opponent_username: str


class PvpStakeRequest(BaseModel):
    battle_id: int
    user_card_ids: list[int]


class PvpBattleIdRequest(BaseModel):
    battle_id: int


@router.get("/pvp/battles")
async def list_battles(user: User = Depends(get_current_user)):
    from db.models import PvpBattle

    async with AsyncSessionLocal() as session:
        incoming = (await session.execute(
            select(PvpBattle).where(
                PvpBattle.opponent_id == user.id,
                PvpBattle.status == "pending",
            ).order_by(PvpBattle.created_at.desc()).limit(20)
        )).scalars().all()

        outgoing = (await session.execute(
            select(PvpBattle).where(
                PvpBattle.challenger_id == user.id,
                PvpBattle.status == "pending",
            ).order_by(PvpBattle.created_at.desc()).limit(20)
        )).scalars().all()

        all_ids = set()
        for b in incoming + outgoing:
            all_ids.add(b.challenger_id)
            if b.opponent_id:
                all_ids.add(b.opponent_id)

        users_map = {}
        if all_ids:
            us = (await session.execute(
                select(User).where(User.id.in_(all_ids))
            )).scalars().all()
            users_map = {u.id: u.username for u in us}

    def fmt(b):
        opponent_id = b.opponent_id if b.challenger_id == user.id else b.challenger_id
        return {
            "id": b.id,
            "challenger": users_map.get(b.challenger_id, "?"),
            "opponent": users_map.get(b.opponent_id) if b.opponent_id else None,
            "opponent_username": users_map.get(opponent_id, "?"),
            "direction": "incoming" if b.opponent_id == user.id else "outgoing",
            "money_stake": b.money_stake,
            "created_at": b.created_at.isoformat(),
        }

    return {
        "incoming": [fmt(b) for b in incoming],
        "outgoing": [fmt(b) for b in outgoing],
    }


@router.post("/pvp/duel")
async def create_duel(
    payload: PvpDuelRequest,
    user: User = Depends(get_current_user),
):
    from db.models import PvpBattle, PvpSeason

    opponent_username = payload.opponent_username.lstrip("@").lower()

    if opponent_username == user.username_normalized:
        raise HTTPException(400, "Нельзя вызвать себя")

    async with AsyncSessionLocal() as session:
        opponent = (await session.execute(
            select(User).where(User.username_normalized == opponent_username)
        )).scalar_one_or_none()

        if opponent is None:
            raise HTTPException(404, f"@{opponent_username} не найден")

        if user.balance < settings.PVP_FEE:
            raise HTTPException(400, f"Нужно {settings.PVP_FEE} монет")

        season = (await session.execute(
            select(PvpSeason).where(PvpSeason.is_active == True)
        )).scalar_one_or_none()

        battle = PvpBattle(
            challenger_id=user.id,
            opponent_id=opponent.id,
            status="pending",
            money_stake=settings.PVP_FEE,
            season_id=season.id if season else None,
        )
        session.add(battle)
        await session.commit()
        await session.refresh(battle)

        return {
            "ok": True,
            "battle_id": battle.id,
            "opponent": opponent.username,
        }


@router.post("/pvp/find")
async def find_opponent(user: User = Depends(get_current_user)):
    from db.models import PvpBattle, PvpSeason
    import random

    async with AsyncSessionLocal() as session:
        min_rating = max(0, user.pvp_rating - 200)
        max_rating = user.pvp_rating + 200

        candidates = (await session.execute(
            select(User)
            .where(
                User.id != user.id,
                User.ban_level == "none",
                User.pvp_rating >= min_rating,
                User.pvp_rating <= max_rating,
            )
            .limit(20)
        )).scalars().all()

        if not candidates:
            raise HTTPException(404, "Не найдено противников")

        opponent = random.choice(candidates)

        if user.balance < settings.PVP_FEE:
            raise HTTPException(400, f"Нужно {settings.PVP_FEE} монет")

        season = (await session.execute(
            select(PvpSeason).where(PvpSeason.is_active == True)
        )).scalar_one_or_none()

        battle = PvpBattle(
            challenger_id=user.id,
            opponent_id=opponent.id,
            status="pending",
            money_stake=settings.PVP_FEE,
            season_id=season.id if season else None,
        )
        session.add(battle)
        await session.commit()
        await session.refresh(battle)

        return {
            "ok": True,
            "battle_id": battle.id,
            "opponent": opponent.username,
        }


@router.get("/pvp/battle/{battle_id}")
async def get_battle(
    battle_id: int,
    user: User = Depends(get_current_user),
):
    from db.models import PvpBattle, PvpStake, UserCard as UC, Card as C

    async with AsyncSessionLocal() as session:
        battle = await session.get(PvpBattle, battle_id)
        if battle is None:
            raise HTTPException(404, "Battle not found")

        if user.id not in (battle.challenger_id, battle.opponent_id):
            raise HTTPException(403, "Not your battle")

        challenger = await session.get(User, battle.challenger_id)
        opponent = await session.get(User, battle.opponent_id) if battle.opponent_id else None

        my_cards = (await session.execute(
            select(UC, C)
            .join(C, UC.card_id == C.id)
            .where(
                UC.user_id == user.id,
                UC.is_locked == False,
            )
            .order_by(C.current_price.desc())
            .limit(30)
        )).all()

        my_stakes = (await session.execute(
            select(PvpStake)
            .where(
                PvpStake.battle_id == battle.id,
                PvpStake.user_id == user.id,
            )
        )).scalars().all()
        chosen_ids = {s.user_card_id for s in my_stakes}

    return {
        "id": battle.id,
        "status": battle.status,
        "challenger": challenger.username if challenger else "?",
        "opponent": opponent.username if opponent else None,
        "challenger_ready": battle.challenger_ready,
        "opponent_ready": battle.opponent_ready,
        "money_stake": battle.money_stake,
        "my_cards": [
            {
                "user_card_id": uc.id,
                "card_id": c.id,
                "name": c.name,
                "rarity": c.rarity,
                "price": c.current_price,
                "image_url": f"/api/cards/{c.id}/image" if c.image_file_id else None,
                "is_chosen": uc.id in chosen_ids,
            }
            for uc, c in my_cards
        ],
        "chosen_count": len(chosen_ids),
        "max_stakes": settings.PVP_MAX_STAKES_PER_SIDE,
    }


@router.post("/pvp/stake")
async def toggle_stake(
    payload: PvpStakeRequest,
    user: User = Depends(get_current_user),
):
    from db.models import PvpBattle, PvpStake, UserCard as UC

    async with AsyncSessionLocal() as session:
        battle = await session.get(PvpBattle, payload.battle_id)
        if battle is None or battle.status != "pending":
            raise HTTPException(404, "Battle not found")

        if user.id not in (battle.challenger_id, battle.opponent_id):
            raise HTTPException(403, "Not your battle")

        side = "challenger" if battle.challenger_id == user.id else "opponent"

        existing = None
        for card_id in payload.user_card_ids:
            s = (await session.execute(
                select(PvpStake).where(
                    PvpStake.battle_id == battle.id,
                    PvpStake.user_card_id == card_id,
                )
            )).scalar_one_or_none()
            if s:
                existing = s
                break

        if existing:
            uc = await session.get(UC, existing.user_card_id)
            if uc:
                uc.is_locked = False
            await session.delete(existing)
            await session.commit()
            return {"ok": True, "action": "removed"}

        current_stakes = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle.id,
                PvpStake.user_id == user.id,
            )
        )).scalars().all()

        if len(current_stakes) >= settings.PVP_MAX_STAKES_PER_SIDE:
            raise HTTPException(400, f"Максимум {settings.PVP_MAX_STAKES_PER_SIDE} карт")

        for card_id in payload.user_card_ids:
            uc = (await session.execute(
                select(UC).where(
                    UC.id == card_id,
                    UC.user_id == user.id,
                    UC.is_locked == False,
                )
            )).scalar_one_or_none()

            if uc is None:
                continue

            uc.is_locked = True
            session.add(PvpStake(
                battle_id=battle.id,
                user_id=user.id,
                user_card_id=card_id,
                side=side,
            ))

        await session.commit()
        return {"ok": True, "action": "added"}


@router.post("/pvp/ready")
async def set_ready(
    payload: PvpBattleIdRequest,
    user: User = Depends(get_current_user),
):
    from db.models import PvpBattle, PvpStake

    async with AsyncSessionLocal() as session:
        battle = await session.get(PvpBattle, payload.battle_id)
        if battle is None or battle.status != "pending":
            raise HTTPException(404, "Battle not found")

        if user.id not in (battle.challenger_id, battle.opponent_id):
            raise HTTPException(403, "Not your battle")

        side = "challenger" if battle.challenger_id == user.id else "opponent"

        my_stakes = (await session.execute(
            select(PvpStake).where(
                PvpStake.battle_id == battle.id,
                PvpStake.user_id == user.id,
            )
        )).scalars().all()

        if not my_stakes:
            raise HTTPException(400, "Поставь хотя бы одну карту")

        if side == "challenger":
            battle.challenger_ready = True
        else:
            battle.opponent_ready = True

        both_ready = battle.challenger_ready and battle.opponent_ready

        if both_ready:
            await _run_battle(session, battle)

        await session.commit()

        return {"ok": True, "both_ready": both_ready}


@router.post("/pvp/decline")
async def decline_battle(
    payload: PvpBattleIdRequest,
    user: User = Depends(get_current_user),
):
    from db.models import PvpBattle, PvpStake, UserCard as UC

    async with AsyncSessionLocal() as session:
        battle = await session.get(PvpBattle, payload.battle_id)
        if battle is None or battle.status != "pending":
            raise HTTPException(404, "Battle not found")

        if battle.opponent_id != user.id and battle.challenger_id != user.id:
            raise HTTPException(403, "Not your battle")

        battle.status = "declined"

        stakes = (await session.execute(
            select(PvpStake).where(PvpStake.battle_id == battle.id)
        )).scalars().all()

        for s in stakes:
            uc = await session.get(UC, s.user_card_id)
            if uc:
                uc.is_locked = False

        await session.commit()

    return {"ok": True}


async def _run_battle(session, battle):
    import random
    from db.models import PvpStake, UserCard as UC
    from services.pvp import calculate_elo, calculate_pvp_money_prize

    challenger = await session.get(User, battle.challenger_id)
    opponent = await session.get(User, battle.opponent_id)

    if challenger is None or opponent is None:
        battle.status = "expired"
        return

    cr = random.randint(1, 6) + random.randint(1, 6)
    orr = random.randint(1, 6) + random.randint(1, 6)

    while cr == orr:
        cr = random.randint(1, 6) + random.randint(1, 6)
        orr = random.randint(1, 6) + random.randint(1, 6)

    if cr > orr:
        winner, loser = challenger, opponent
        winner_side, loser_side = "challenger", "opponent"
    else:
        winner, loser = opponent, challenger
        winner_side, loser_side = "opponent", "challenger"

    elo = calculate_elo(winner.pvp_rating, loser.pvp_rating)
    winner_delta = elo.winner_delta
    loser_delta = elo.loser_delta

    if winner.plus_tier == "indy_plus":
        winner_delta = int(winner_delta * settings.PLUS_PVP_MULTIPLIER)
    if loser.plus_tier == "indy_plus":
        loser_delta = int(loser_delta / settings.PLUS_PVP_MULTIPLIER)

    winner.pvp_rating += winner_delta
    loser.pvp_rating = max(100, loser.pvp_rating + loser_delta)
    winner.pvp_wins += 1
    winner.pvp_wins_total += 1
    loser.pvp_losses += 1
    loser.pvp_losses_total += 1

    loser_stakes = (await session.execute(
        select(PvpStake).where(
            PvpStake.battle_id == battle.id,
            PvpStake.side == loser_side,
        )
    )).scalars().all()

    cards_transferred = 0
    for s in loser_stakes:
        uc = await session.get(UC, s.user_card_id)
        if uc:
            uc.user_id = winner.id
            uc.is_locked = False
            cards_transferred += 1

    winner_stakes = (await session.execute(
        select(PvpStake).where(
            PvpStake.battle_id == battle.id,
            PvpStake.side == winner_side,
        )
    )).scalars().all()

    for s in winner_stakes:
        uc = await session.get(UC, s.user_card_id)
        if uc:
            uc.is_locked = False

    money_prize = calculate_pvp_money_prize(
        battle.money_stake, battle.money_stake,
        commission=settings.PVP_BANK_COMMISSION,
    )
    winner.balance += money_prize
    loser.balance -= battle.money_stake

    battle.status = "finished"
    battle.challenger_roll = cr
    battle.opponent_roll = orr
    battle.winner_id = winner.id
    battle.finished_at = datetime.utcnow()


# ═════════════════════════════════════════════
# RATING
# ═════════════════════════════════════════════

@router.get("/rating")
async def get_rating(user: User = Depends(get_current_user)):
    async with AsyncSessionLocal() as session:
        money_top = (await session.execute(
            select(User).order_by(User.balance.desc()).limit(10)
        )).scalars().all()

        season_top = (await session.execute(
            select(User).order_by(User.pvp_rating.desc()).limit(10)
        )).scalars().all()

        eternal_top = (await session.execute(
            select(User).order_by(User.pvp_wins_total.desc()).limit(10)
        )).scalars().all()

    def fmt(u, i):
        return {
            "rank": i + 1,
            "username": u.username,
            "balance": u.balance,
            "pvp_rating": u.pvp_rating,
            "pvp_wins_total": u.pvp_wins_total,
            "pvp_losses_total": u.pvp_losses_total,
            "collection_value": 0,
        }

    return {
        "money": [fmt(u, i) for i, u in enumerate(money_top)],
        "season": [fmt(u, i) for i, u in enumerate(season_top)],
        "eternal": [fmt(u, i) for i, u in enumerate(eternal_top)],
    }


# ═════════════════════════════════════════════
# CLAN
# ═════════════════════════════════════════════

class ClanCreateRequest(BaseModel):
    name: str
    tag: str


class ClanJoinRequest(BaseModel):
    clan_id: int


@router.get("/clan/my")
async def clan_my(user: User = Depends(get_current_user)):
    from db.models import Clan, ClanMember

    async with AsyncSessionLocal() as session:
        member = (await session.execute(
            select(ClanMember).where(ClanMember.user_id == user.id)
        )).scalar_one_or_none()

        if member is None:
            return {"clan": None, "role": None}

        clan = await session.get(Clan, member.clan_id)
        if clan is None:
            return {"clan": None, "role": None}

        count = (await session.execute(
            select(func.count(ClanMember.id)).where(ClanMember.clan_id == clan.id)
        )).scalar() or 0

        owner = await session.get(User, clan.owner_id)

    return {
        "clan": {
            "id": clan.id,
            "name": clan.name,
            "tag": clan.tag,
            "level": clan.level,
            "xp": clan.xp,
            "treasury": clan.treasury,
            "members_count": count,
            "is_open": clan.is_open,
            "owner": owner.username if owner else "?",
        },
        "role": member.role,
    }


@router.get("/clan/list")
async def clan_list(user: User = Depends(get_current_user)):
    from db.models import Clan, ClanMember

    async with AsyncSessionLocal() as session:
        clans = (await session.execute(
            select(Clan).where(Clan.is_active == True).order_by(Clan.xp.desc()).limit(30)
        )).scalars().all()

        result = []
        for c in clans:
            count = (await session.execute(
                select(func.count(ClanMember.id)).where(ClanMember.clan_id == c.id)
            )).scalar() or 0
            owner = await session.get(User, c.owner_id)
            result.append({
                "id": c.id,
                "name": c.name,
                "tag": c.tag,
                "level": c.level,
                "xp": c.xp,
                "treasury": c.treasury,
                "members_count": count,
                "is_open": c.is_open,
                "owner": owner.username if owner else "?",
            })

    return result


@router.post("/clan/create")
async def clan_create(
    payload: ClanCreateRequest,
    user: User = Depends(get_current_user),
):
    from services.clan import create_clan

    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        result = await create_clan(session, user_row, payload.name, payload.tag, None)

        if not result.ok:
            raise HTTPException(400, result.reason)

        return {"ok": True, "clan_id": result.clan_id}


@router.post("/clan/join")
async def clan_join(
    payload: ClanJoinRequest,
    user: User = Depends(get_current_user),
):
    from services.clan import join_clan

    async with AsyncSessionLocal() as session:
        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        result = await join_clan(session, user_row, payload.clan_id)

        if not result.ok:
            raise HTTPException(400, result.reason)

        return {"ok": True, "clan_id": result.clan_id}


# ═════════════════════════════════════════════
# AUCTION
# ═════════════════════════════════════════════

class AuctionBidRequest(BaseModel):
    lot_id: int
    amount: int


class AuctionBuyoutRequest(BaseModel):
    lot_id: int


@router.get("/auction/list")
async def auction_list(user: User = Depends(get_current_user)):
    from db.models import Auction

    async with AsyncSessionLocal() as session:
        lots = (await session.execute(
            select(Auction).where(
                Auction.status == "active",
                Auction.ends_at > datetime.utcnow(),
            ).order_by(Auction.ends_at.asc()).limit(30)
        )).scalars().all()

        result = []
        for lot in lots:
            seller = await session.get(User, lot.seller_id)
            bidder = await session.get(User, lot.current_bidder_id) if lot.current_bidder_id else None

            uc = await session.get(UserCard, lot.user_card_id)
            card = await session.get(Card, uc.card_id) if uc else None

            if card is None:
                continue

            ends_in = int((lot.ends_at - datetime.utcnow()).total_seconds() / 60)

            result.append({
                "id": lot.id,
                "seller": seller.username if seller else "?",
                "card_id": card.id,
                "card_name": card.name,
                "rarity": card.rarity,
                "image_url": f"/api/cards/{card.id}/image" if card.image_file_id else None,
                "start_price": lot.start_price,
                "buyout_price": lot.buyout_price,
                "current_bid": lot.current_bid,
                "current_bidder": bidder.username if bidder else None,
                "bid_count": lot.bid_count,
                "ends_at": lot.ends_at.isoformat(),
                "ends_in_minutes": ends_in,
            })

    return result


@router.post("/auction/bid")
async def auction_bid(
    payload: AuctionBidRequest,
    user: User = Depends(get_current_user),
):
    from db.models import Auction, AuctionBid

    async with AsyncSessionLocal() as session:
        lot = await session.get(Auction, payload.lot_id)
        if lot is None or lot.status != "active":
            raise HTTPException(404, "Лот не найден")

        if lot.seller_id == user.id:
            raise HTTPException(400, "Нельзя ставить на свой лот")

        min_bid = int(lot.current_bid * 1.05) if lot.current_bid else lot.start_price

        if payload.amount < min_bid:
            raise HTTPException(400, f"Минимум {min_bid:,}")

        if user.balance < payload.amount:
            raise HTTPException(400, f"Нужно {payload.amount:,}")

        if lot.current_bidder_id:
            prev = await session.get(User, lot.current_bidder_id)
            if prev:
                prev.balance += lot.current_bid

        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        user_row.balance -= payload.amount
        lot.current_bid = payload.amount
        lot.current_bidder_id = user_row.id
        lot.bid_count += 1

        session.add(AuctionBid(
            auction_id=lot.id,
            bidder_id=user_row.id,
            amount=payload.amount,
        ))

        await session.commit()

    return {"ok": True, "amount": payload.amount}


@router.post("/auction/buyout")
async def auction_buyout(
    payload: AuctionBuyoutRequest,
    user: User = Depends(get_current_user),
):
    from db.models import Auction

    async with AsyncSessionLocal() as session:
        lot = await session.get(Auction, payload.lot_id)
        if lot is None or lot.status != "active" or not lot.buyout_price:
            raise HTTPException(404, "Выкуп недоступен")

        if lot.seller_id == user.id:
            raise HTTPException(400, "Нельзя выкупить свой лот")

        user_row = await session.get(User, user.id)
        if user_row is None:
            raise HTTPException(404, "User not found")

        if user_row.balance < lot.buyout_price:
            raise HTTPException(400, f"Нужно {lot.buyout_price:,}")

        if lot.current_bidder_id:
            prev = await session.get(User, lot.current_bidder_id)
            if prev:
                prev.balance += lot.current_bid

        seller = await session.get(User, lot.seller_id)
        commission = 10.0
        fee = int(lot.buyout_price * commission / 100)

        user_row.balance -= lot.buyout_price
        if seller:
            seller.balance += lot.buyout_price - fee

        uc = await session.get(UserCard, lot.user_card_id)
        if uc:
            uc.user_id = user_row.id
            uc.is_locked = False

        lot.status = "sold"
        lot.sold_at = datetime.utcnow()

        await session.commit()

    return {"ok": True, "price": lot.buyout_price}


# ═════════════════════════════════════════════
# NOTIFICATIONS (для Visual Merge)
# ═════════════════════════════════════════════

class MarkReadRequest(BaseModel):
    notification_id: int


@router.get("/notifications")
async def get_notifications(user: User = Depends(get_current_user)):
    """
    Последние уведомления игрока.

    Возвращает:
      items[]  — список уведомлений (до 30)
      unread   — количество непрочитанных
    """
    items = await get_user_notifications(user.id, limit=30)
    unread = await get_unread_count(user.id)

    return {
        "items": [
            {
                "id": n.id,
                "type": n.type,
                "title": n.title,
                "text": n.text,
                "icon": n.icon,
                "color": n.color,
                "payload": n.payload,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat(),
            }
            for n in items
        ],
        "unread": unread,
    }


@router.post("/notifications/read")
async def read_notification(
    payload: MarkReadRequest,
    user: User = Depends(get_current_user),
):
    """Помечает одно уведомление прочитанным."""
    ok = await mark_read(user.id, payload.notification_id)
    if not ok:
        raise HTTPException(404, "Уведомление не найдено")

    unread = await get_unread_count(user.id)
    return {"ok": True, "unread": unread}


@router.delete("/notifications/clear")
async def clear_notifications(user: User = Depends(get_current_user)):
    """Удаляет все уведомления игрока."""
    deleted = await clear_user_notifications(user.id)
    return {"ok": True, "deleted": deleted, "unread": 0}


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
