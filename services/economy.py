from core.constants import IW_MULTIPLIER, FLOOR_MULTIPLIER, CEILING_MULTIPLIER

def calculate_price(base_price: int, demand: int = 0, supply: int = 0, event: float = 1.0, is_iw: bool = False) -> int:
    iw = IW_MULTIPLIER if is_iw else 1
    ratio = (demand / supply) if supply > 0 and demand > 0 else (2.0 if demand > 0 else 1.0)
    ratio = max(0.3, min(ratio, 3.0))
    price = base_price * ratio * event * iw
    floor = int(base_price * FLOOR_MULTIPLIER)
    ceiling = int(base_price * CEILING_MULTIPLIER)
    return int(max(floor, min(price, ceiling)))

def decay_price(current: int, base: int, rate: float = 0.05) -> int:
    diff = current - base
    if abs(diff) < base * 0.01:
        return base
    return int(current - diff * rate) 
