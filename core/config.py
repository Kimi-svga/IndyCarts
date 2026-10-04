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
    BANK_RATE: float = 0.10
    BANK_MAX_LOAN: int = 50000
    BANK_TERM_DAYS: int = 30
    SHOP_COIN_PER_ATTEMPT: int = 50
    MAX_ATTEMPTS_PER_DAY: int = 10

    REFERRAL_BONUS_MONEY: int = 500
    REFERRAL_BONUS_ATTEMPTS: int = 1
    REFERRAL_MAX_PER_DAY: int = 10

    # ─── Indy+ (патч 0.8.0) ───
    PLUS_PRICE_STARS: int = 20
    PLUS_PRICE_COINS: int = 200_000
    PLUS_DURATION_DAYS: int = 30
    PLUS_BONUS_ATTEMPTS: int = 5
    PLUS_PVP_MULTIPLIER: float = 1.2
    PLUS_ROYALTY_PERCENT: float = 7.0
    PLUS_AUCTION_COMMISSION: float = 5.0
    PLUS_DAILY_ATTEMPTS: int = 5


settings = Settings() 
