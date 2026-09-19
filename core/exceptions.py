"""Свои исключения для Indy Carts."""


class IndyCartsError(Exception):
    """Базовая ошибка проекта."""
    pass


class InsufficientFunds(IndyCartsError):
    """Недостаточно монет."""
    pass


class CardNotFound(IndyCartsError):
    """Карта не найдена."""
    pass


class MergeFailed(IndyCartsError):
    """Слияние не удалось."""
    pass


class UserNotFound(IndyCartsError):
    """Игрок не найден."""
    pass


class BattleNotActive(IndyCartsError):
    """Дуэль неактивна."""
    pass 
