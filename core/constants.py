"""Константы игры."""

# Редкости
RARITY_COMMON = "common"
RARITY_RARE = "rare"
RARITY_EPIC = "epic"
RARITY_LEGENDARY = "legendary"
RARITY_ULTRA = "ultra"

RARITIES = [RARITY_COMMON, RARITY_RARE, RARITY_EPIC, RARITY_LEGENDARY, RARITY_ULTRA]

RARITY_NAMES = {
    RARITY_COMMON: "Common",
    RARITY_RARE: "Rare",
    RARITY_EPIC: "Epic",
    RARITY_LEGENDARY: "Legendary",
    RARITY_ULTRA: "Ultra",
}

RARITY_EMOJI = {
    RARITY_COMMON: "⚪",
    RARITY_RARE: "🔵",
    RARITY_EPIC: "🟣",
    RARITY_LEGENDARY: "🟡",
    RARITY_ULTRA: "🔴",
}

# Базовые цены
BASE_PRICES = {
    RARITY_COMMON: 100,
    RARITY_RARE: 300,
    RARITY_EPIC: 1000,
    RARITY_LEGENDARY: 5000,
    RARITY_ULTRA: 20000,
}

# Шансы дропа
DROP_CHANCES = {
    RARITY_COMMON: 50,
    RARITY_RARE: 25,
    RARITY_EPIC: 15,
    RARITY_LEGENDARY: 7,
    RARITY_ULTRA: 3,
}

IW_CHANCE = 5
IW_MULTIPLIER = 3
FLOOR_MULTIPLIER = 0.3
CEILING_MULTIPLIER = 5.0

# Комиссии
MARKET_FEE = 0.03
AUCTION_FEE = 0.07

# Зарезервированные юзы
RESERVED_USERNAMES = {
    "owner", "admin", "administrator", "mod", "moderator",
    "support", "help", "staff", "team", "official",
    "system", "root", "superuser", "bot",
    "p49", "p4_9", "p4dev", "indycarts", "indy_carts",
    "bank", "credit", "auction", "market", "exchange",
}

# Юзы
USERNAME_PATTERN = r"^[A-Za-z][A-Za-z0-9_]{2,19}$"
