from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    BOT_TOKEN: str
    WEBHOOK_URL: str
    WEBHOOK_SECRET: str
    ADMIN_IDS: list[int] = []
    OWNER_IDS: list[int] = []
    DATABASE_URL: str

    PORT: int = 8000
    DAILY_MONEY: int = 450
    DAILY_ATTEMPTS: int = 2
    PVP_FEE: int = 10
    SHOP_COIN_PER_ATTEMPT: int = 50
    MAX_ATTEMPTS_PER_DAY: int = 10

    REFERRAL_BONUS_MONEY: int = 500
    REFERRAL_BONUS_ATTEMPTS: int = 1
    REFERRAL_MAX_PER_DAY: int = 10

    # Indy+ (0.8.0)
    PLUS_PRICE_STARS: int = 20
    PLUS_PRICE_COINS: int = 200_000
    PLUS_DURATION_DAYS: int = 30
    PLUS_BONUS_ATTEMPTS: int = 5
    PLUS_PVP_MULTIPLIER: float = 1.2
    PLUS_ROYALTY_PERCENT: float = 7.0
    PLUS_AUCTION_COMMISSION: float = 5.0
    PLUS_DAILY_ATTEMPTS: int = 5

    # Банк 2.0 (0.9.0)
    BANK_MAX_LOAN: int = 500_000
    BANK_ABS_MAX_LOAN: int = 1_000_000
    BANK_EARLY_DISCOUNT: float = 0.02
    BANK_OVERDUE_TRUST_PENALTY: int = 15
    BANK_DEFAULT_TRUST_PENALTY: int = 50
    BANK_OVERDUE_CARDS_CONFISCATE: int = 10
    BANK_PVP_BLOCK_DAYS: int = 7
    BANK_REFINANCE_COOLDOWN_DAYS: int = 3


settings = Settings() 
