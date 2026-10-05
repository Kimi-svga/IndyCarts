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

MAIN_MENU_TITLE = "🏁 <b>Indy Carts</b>"

MAIN_MENU_BUTTONS = [
    ("👤 Профиль",   "profile"),
    ("🃏 Карты",     "cards"),
    ("💹 Биржа",     "market"),
    ("🛒 Магазин",   "shop"),
    ("⚔️ PvP",       "pvp"),
    ("🏦 Банк",      "bank"),
    ("🏆 Рейтинг",   "rating"),
    ("👥 Рефералка", "ref"),
    ("📅 Ежедневка", "daily"),
    ("💎 Indy+",     "plus"),
]

# Банк
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

# PvP 2.0 (1.0.0)
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
# Роли админов
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


# ─────────────────────────────────────────────
# Ban Hammer · Автоправила
# ─────────────────────────────────────────────

BAN_BAD_WORDS = {
    "fuck", "shit", "bitch", "asshole",
    "бля", "хуй", "пизда", "ебать", "сука",
    "дурак", "идиот",
}

BAN_WARN_THRESHOLD = 3
BAN_SPAM_THRESHOLD = 10
BAN_WINTRADING_PAIRS = 5
