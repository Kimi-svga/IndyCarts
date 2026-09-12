"""Формулы цены карты."""

from core.constants import IW_MULTIPLIER, FLOOR_MULTIPLIER, CEILING_MULTIPLIER


def calculate_price(
    base_price: int,
    demand: int = 0,
    supply: int = 0,
    event_modifier: float = 1.0,
    is_iw: bool = False,
) -> int:
    """Считает текущую цену карты с floor и ceiling."""
    iw_mult = IW_MULTIPLIER if is_iw else 1

    if supply == 0:
        ratio = 2.0 if demand > 0 else 1.0
    else:
        ratio = demand / supply if demand > 0 else 0.5

    ratio = max(0.3, min(ratio, 3.0))

    price = base_price * ratio * event_modifier * iw_mult

    floor = int(base_price * FLOOR_MULTIPLIER)
    ceiling = int(base_price * CEILING_MULTIPLIER)

    return int(max(floor, min(price, ceiling)))
