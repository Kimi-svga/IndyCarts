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

    PLUS_PRICE_STARS: int = 20
    PLUS_PRICE_COINS: int = 200_000
    PLUS_DURATION_DAYS: int = 30
    PLUS_BONUS_ATTEMPTS: int = 5
    PLUS_PVP_MULTIPLIER: float = 1.2
    PLUS_ROYALTY_PERCENT: float = 7.0
    PLUS_AUCTION_COMMISSION: float = 5.0
    PLUS_DAILY_ATTEMPTS: int = 5

    BANK_MAX_LOAN: int = 500_000
    BANK_ABS_MAX_LOAN: int = 1_000_000
    BANK_EARLY_DISCOUNT: float = 0.02
    BANK_OVERDUE_TRUST_PENALTY: int = 15
    BANK_DEFAULT_TRUST_PENALTY: int = 50
    BANK_OVERDUE_CARDS_CONFISCATE: int = 10
    BANK_PVP_BLOCK_DAYS: int = 7
    BANK_REFINANCE_COOLDOWN_DAYS: int = 3

    PVP_SEASON_DAYS: int = 30
    PVP_SEASON_RESET_RATING: int = 1000
    PVP_MAX_STAKES_PER_SIDE: int = 3
    PVP_BANK_COMMISSION: float = 0.10
    PVP_TIMEOUT_MINUTES: int = 10

    BAN_WARN_DURATION_DAYS: int = 30
    BAN_MUTE_DEFAULT_HOURS: int = 24
    BAN_DEFAULT_DAYS: int = 30
    BAN_DEFAULT_CONFISCATE_CARDS: int = 0

    SUPPORT_TICKET_COOLDOWN_MIN: int = 15
    SUPPORT_TICKET_MAX_OPEN: int = 2
    SUPPORT_TICKET_AUTO_CLOSE_HOURS: int = 72
    SUPPORT_REPUTATION_PER_RESOLVE: int = 5

    TRADE_MAX_CARDS: int = 5
    TRADE_MAX_MONEY: int = 1_000_000
    TRADE_TIMEOUT_HOURS: int = 24

    AUCTION_MIN_STEP_PERCENT: float = 0.05
    AUCTION_COMMISSION: float = 10.0
    AUCTION_COMMISSION_PLUS: float = 5.0
    AUCTION_MIN_PRICE: int = 10
    AUCTION_MAX_PRICE: int = 10_000_000

    CREATOR_DURATION_DAYS: int = 30
    CREATOR_MAX_CARDS_PER_DAY: int = 3
    CREATOR_START_MONEY: int = 5000

    CARD_SEARCH_LIMIT: int = 15
    CARD_LIST_PER_PAGE: int = 10
    CARD_TEAMS_PER_PAGE: int = 8
    CARD_YEARS_PER_PAGE: int = 8

    # ─── Clans (v1.5.0) ───
    CLAN_CREATE_PRICE: int = 200_000
    CLAN_CREATE_FREE_FOR_PLUS: bool = True
    CLAN_INVITE_TIMEOUT_HOURS: int = 48
    CLAN_TOP_LIMIT: int = 10


settings = Settings() 
