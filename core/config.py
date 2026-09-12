from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    
    BOT_TOKEN: str
    WEBHOOK_URL: str
    WEBHOOK_SECRET: str
    ADMIN_IDS: list[int] = []

    
    DATABASE_URL: str

    # Game
    PORT: int = 8000
    DAILY_MONEY: int = 450
    DAILY_ATTEMPTS: int = 2
    PVP_FEE: int = 10
    BANK_RATE: float = 0.10
    BANK_MAX_LOAN: int = 50000
    BANK_TERM_DAYS: int = 30


settings = Settings()
