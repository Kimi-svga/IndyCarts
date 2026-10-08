"""Константы игры."""

RARITY_BASIC = "basic"
RARITY_RARE = "rare"
RARITY_EPIC = "epic"
RARITY_MYTHIC = "mythic"
RARITY_LEGENDARY = "legendary"
RARITY_LIMITED = "limited"
RARITY_SEASON = "season"

RARITIES = [
    RARITY_BASIC, RARITY_RARE, RARITY_EPIC, RARITY_MYTHIC,
    RARITY_LEGENDARY, RARITY_LIMITED, RARITY_SEASON,
]

RARITY_NAMES = {
    RARITY_BASIC: "Basic",
    RARITY_RARE: "Rare",
    RARITY_EPIC: "Epic",
    RARITY_MYTHIC: "Mythic",
    RARITY_LEGENDARY: "Legendary",
    RARITY_LIMITED: "Limited",
    RARITY_SEASON: "Season",
}

RARITY_EMOJI = {
    RARITY_BASIC: "🔵",
    RARITY_RARE: "🟢",
    RARITY_EPIC: "🟣",
    RARITY_MYTHIC: "🟠",
    RARITY_LEGENDARY: "🟡",
    RARITY_LIMITED: "🔴",
    RARITY_SEASON: "⭐",
}

BASE_PRICES = {
    RARITY_BASIC: 100,
    RARITY_RARE: 300,
    RARITY_EPIC: 1000,
    RARITY_MYTHIC: 5000,
    RARITY_LEGENDARY: 20000,
    RARITY_LIMITED: 50000,
    RARITY_SEASON: 100000,
}

DROP_CHANCES = {
    RARITY_BASIC: 50,
    RARITY_RARE: 25,
    RARITY_EPIC: 15,
    RARITY_MYTHIC: 7,
    RARITY_LEGENDARY: 2.5,
    RARITY_LIMITED: 0.5,
    RARITY_SEASON: 0,
}

IW_CHANCE = 5
IW_MULTIPLIER = 3
FLOOR_MULTIPLIER = 0.3
CEILING_MULTIPLIER = 5.0
MARKET_FEE = 0.10
PVP_FEE = 10

MERGE_RULES = {
    RARITY_BASIC: {"result": RARITY_RARE, "chance": 0.7},
    RARITY_RARE: {"result": RARITY_EPIC, "chance": 0.7},
    RARITY_EPIC: {"result": RARITY_MYTHIC, "chance": 0.7},
    RARITY_MYTHIC: {"result": RARITY_LEGENDARY, "chance": 0.7},
    RARITY_LEGENDARY: {"result": RARITY_LIMITED, "chance": 0.2},
}

RESERVED_USERNAMES = {
    "owner", "admin", "support", "mod", "staff", "system", "bot",
    "p49", "indycarts", "bank", "market", "auction", "help", "official",
}

USERNAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_]{2,19}$"


# ─────────────────────────────────────────────
# UI · Главное меню
# ─────────────────────────────────────────────

MAIN_MENU_TITLE = "🏁 <b>Indy Carts</b>"

MAIN_MENU_BUTTONS = [
    ("👤 Профиль",   "profile"),
    ("🃏 Карты",     "cards"),
    ("💹 Биржа",     "market"),
    ("🎯 Аукцион",   "auction"),
    ("🛒 Магазин",   "shop"),
    ("⚔️ PvP",       "pvp"),
    ("🏦 Банк",      "bank"),
    ("🏰 Кланы",     "clans"),
    ("🏆 Рейтинг",   "rating"),
    ("👥 Рефералка", "ref"),
    ("📅 Ежедневка", "daily"),
    ("💎 Indy+",     "plus"),
]


# ─────────────────────────────────────────────
# Банк
# ─────────────────────────────────────────────

LOAN_RATES = [
    (50_000,       0.15),
    (200_000,      0.20),
    (500_000,      0.25),
    (float("inf"), 0.30),
]

LOAN_TERMS = [
    (50_000,       7),
    (200_000,      14),
    (500_000,      30),
    (float("inf"), 45),
]

TRUST_RANKS = [
    (-999,         "⛔ Чёрный список"),
    (0,            "🥉 Новичок"),
    (20,           "🥈 Надёжный"),
    (50,           "🥇 Отличный"),
    (100,          "💎 Премиум"),
    (200,          "👑 Элита банка"),
]

TRUST_DELTA = {
    "early_repay":   +10,
    "on_time":       +5,
    "big_repay":     +15,
    "overdue":       -15,
    "refinance":     -3,
    "default":       -50,
}


# ─────────────────────────────────────────────
# PvP
# ─────────────────────────────────────────────

PVP_TITLES = [
    (2000, "👑 Легенда"),
    (1800, "🏆 Чемпион"),
    (1600, "⭐ Элита"),
    (1400, "🔥 Про"),
    (1200, "🟢 Новичок"),
    (0,    "⚪ Стажёр"),
]

PVP_SEASON_REWARDS = {
    1:  {"money": 100_000, "attempts": 50, "card": True,  "title": "👑 Чемпион"},
    2:  {"money": 75_000,  "attempts": 30, "card": False, "title": "🥈 Вице-чемпион"},
    3:  {"money": 50_000,  "attempts": 20, "card": False, "title": "🥉 Бронза"},
    4:  {"money": 30_000,  "attempts": 10, "card": False, "title": None},
    5:  {"money": 30_000,  "attempts": 10, "card": False, "title": None},
    6:  {"money": 15_000,  "attempts": 5,  "card": False, "title": None},
    7:  {"money": 15_000,  "attempts": 5,  "card": False, "title": None},
    8:  {"money": 15_000,  "attempts": 5,  "card": False, "title": None},
    9:  {"money": 15_000,  "attempts": 5,  "card": False, "title": None},
    10: {"money": 15_000,  "attempts": 5,  "card": False, "title": None},
}


# ─────────────────────────────────────────────
# Роли
# ─────────────────────────────────────────────

ROLE_LEVELS = {
    "owner": 100,
    "admin": 80,
    "moderator": 60,
    "helper": 40,
    "support": 30,
}

ROLE_EMOJI = {
    "owner": "👑",
    "admin": "🔴",
    "moderator": "🟡",
    "helper": "🟢",
    "support": "🔵",
}

ROLE_NAMES = {
    "owner": "Владелец",
    "admin": "Администратор",
    "moderator": "Модератор",
    "helper": "Помощник",
    "support": "Поддержка",
}


# ─────────────────────────────────────────────
# Ban Hammer
# ─────────────────────────────────────────────

BAN_LEVELS = {
    "warn": "⚠️",
    "mute": "🔇",
    "ban": "🚫",
}

BAN_NAMES = {
    "warn": "Предупреждение",
    "mute": "Мьют",
    "ban": "Бан",
}

MUTE_DURATIONS = [1, 24, 168]
BAN_DURATIONS = [168, 720, None]

BAN_BAD_WORDS = {
    "fuck", "shit", "bitch", "asshole",
    "бля", "хуй", "пизда", "ебать", "сука",
    "дурак", "идиот",
}

BAN_WARN_THRESHOLD = 3
BAN_SPAM_THRESHOLD = 10
BAN_WINTRADING_PAIRS = 5


# ─────────────────────────────────────────────
# Support System
# ─────────────────────────────────────────────

TICKET_CATEGORIES = {
    "bug":       "🐛 Баг / ошибка",
    "balance":   "💰 Проблема с балансом",
    "cards":     "🃏 Проблема с картами",
    "pvp":       "⚔️ Проблема с PvP",
    "bank":      "🏦 Проблема с банком",
    "plus":      "💎 Проблема с Indy+",
    "report":    "🚨 Жалоба на игрока",
    "apply":     "📋 Заявка в команду",
    "other":     "❓ Другое",
}

TICKET_PRIORITIES = {
    "low":    "🟢 Низкий",
    "normal": "🟡 Обычный",
    "high":   "🟠 Высокий",
    "urgent": "🔴 Срочный",
}

TICKET_STATUSES = {
    "open":     "📬 Открыт",
    "pending":  "⏳ В ожидании",
    "resolved": "✅ Решён",
    "closed":   "🔒 Закрыт",
}

TICKET_COOLDOWN_MINUTES = 15
TICKET_MAX_OPEN = 2
TICKET_AUTO_CLOSE_HOURS = 72


# ─────────────────────────────────────────────
# Trade
# ─────────────────────────────────────────────

TRADE_MAX_CARDS = 5
TRADE_MAX_MONEY = 1_000_000
TRADE_TIMEOUT_HOURS = 24

TRADE_STATUSES = {
    "pending": "⏳ ожидает",
    "accepted": "✅ принят",
    "declined": "❌ отклонён",
    "cancelled": "🚫 отменён",
    "expired": "⌛ истёк",
}


# ─────────────────────────────────────────────
# Auction
# ─────────────────────────────────────────────

AUCTION_DURATIONS = {
    "1h": ("1 час", 1),
    "6h": ("6 часов", 6),
    "24h": ("24 часа", 24),
    "3d": ("3 дня", 72),
}

AUCTION_MIN_BID_STEP = 0.05
AUCTION_COMMISSION = 10.0
AUCTION_COMMISSION_PLUS = 5.0

AUCTION_STATUSES = {
    "active": "🟢 активен",
    "sold": "✅ продан",
    "cancelled": "🚫 отменён",
    "expired": "⌛ истёк",
}


# ─────────────────────────────────────────────
# Clans (v1.5.0)
# ─────────────────────────────────────────────

CLAN_MIN_LEVEL = 1
CLAN_MAX_LEVEL = 10

CLAN_NAME_MIN = 3
CLAN_NAME_MAX = 24
CLAN_TAG_MIN = 2
CLAN_TAG_MAX = 4
CLAN_DESC_MAX = 200

CLAN_CREATE_PRICE = 200_000
CLAN_TOP_LIMIT = 10

CLAN_ROLES = ["leader", "officer", "member"]

CLAN_ROLE_LEVELS = {
    "leader": 100,
    "officer": 60,
    "member": 10,
}

CLAN_ROLE_EMOJI = {
    "leader": "👑",
    "officer": "⚔️",
    "member": "👤",
}

CLAN_ROLE_NAMES = {
    "leader": "Лидер",
    "officer": "Офицер",
    "member": "Участник",
}

# 10 уровней клана.
# xp_required — XP, чтобы ДОСТИЧЬ этого уровня.
# max_members — лимит участников.
# drop_bonus / money_bonus — % бонус к дропу / деньгам.
# auction_discount — % скидка на комиссию аукциона.
# extra_attempts — доп. попытки в день каждому участнику.

CLAN_LEVELS = {
    1:  {"xp_required": 0,          "max_members": 10, "drop_bonus": 0.00, "money_bonus": 0.00, "auction_discount": 0.0, "extra_attempts": 0},
    2:  {"xp_required": 50_000,     "max_members": 15, "drop_bonus": 0.05, "money_bonus": 0.05, "auction_discount": 0.5, "extra_attempts": 0},
    3:  {"xp_required": 150_000,    "max_members": 20, "drop_bonus": 0.10, "money_bonus": 0.10, "auction_discount": 1.0, "extra_attempts": 0},
    4:  {"xp_required": 350_000,    "max_members": 25, "drop_bonus": 0.15, "money_bonus": 0.15, "auction_discount": 1.5, "extra_attempts": 1},
    5:  {"xp_required": 750_000,    "max_members": 30, "drop_bonus": 0.20, "money_bonus": 0.20, "auction_discount": 2.0, "extra_attempts": 1},
    6:  {"xp_required": 1_500_000,  "max_members": 35, "drop_bonus": 0.25, "money_bonus": 0.25, "auction_discount": 2.5, "extra_attempts": 2},
    7:  {"xp_required": 3_000_000,  "max_members": 40, "drop_bonus": 0.30, "money_bonus": 0.30, "auction_discount": 3.0, "extra_attempts": 2},
    8:  {"xp_required": 6_000_000,  "max_members": 45, "drop_bonus": 0.35, "money_bonus": 0.35, "auction_discount": 3.5, "extra_attempts": 3},
    9:  {"xp_required": 12_000_000, "max_members": 50, "drop_bonus": 0.40, "money_bonus": 0.40, "auction_discount": 4.0, "extra_attempts": 3},
    10: {"xp_required": 25_000_000, "max_members": 50, "drop_bonus": 0.50, "money_bonus": 0.50, "auction_discount": 5.0, "extra_attempts": 5},
}

CLAN_INVITE_TIMEOUT_HOURS = 48
CLAN_MAX_INVITES_PENDING = 20

CLAN_ACTIONS = {
    "create":    "🏰 Создание клана",
    "join":      "📥 Вступление",
    "leave":     "📤 Выход",
    "deposit":   "💰 Вклад в казну",
    "kick":      "🚪 Исключение",
    "promote":   "⬆️ Повышение",
    "demote":    "⬇️ Понижение",
    "level_up":  "🎉 Новый уровень",
    "disband":   "💥 Расформирование",
}
