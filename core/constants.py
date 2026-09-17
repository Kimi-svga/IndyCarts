RARITY_BASIC = "basic"
RARITY_RARE = "rare"
RARITY_EPIC = "epic"
RARITY_MYTHIC = "mythic"
RARITY_LEGENDARY = "legendary"
RARITY_LIMITED = "limited"
RARITY_SEASON = "season"

RARITIES = [RARITY_BASIC, RARITY_RARE, RARITY_EPIC, RARITY_MYTHIC, RARITY_LEGENDARY, RARITY_LIMITED, RARITY_SEASON]

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
MARKET_FEE = 0.03
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
