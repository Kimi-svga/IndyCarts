"""Логика дропа карт."""

import random
from core.constants import DROP_CHANCES, IW_CHANCE


def roll_rarity() -> str:
    rarities = list(DROP_CHANCES.keys())
    weights = list(DROP_CHANCES.values())
    return random.choices(rarities, weights=weights, k=1)[0]


def roll_iw() -> bool:
    return random.randint(1, 100) <= IW_CHANCE


def roll_card() -> tuple[str, bool]:
    return roll_rarity(), roll_iw()
