from decimal import Decimal

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    DATABASE_URL: str = "postgresql+asyncpg://polytrade:polytrade_dev@localhost:5432/polytrade"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    ARMORIQ_API_KEY: str = ""
    ARMORIQ_USER_ID: str = ""

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GOOGLE_API_KEY: str = ""
    DEFAULT_LLM_PROVIDER: str = "openai"

    TAVILY_API_KEY: str = ""
    NEWSAPI_KEY: str = ""

    INITIAL_BALANCE: Decimal = Decimal("1000.00")

    POLYMARKET_CLOB_URL: str = "https://clob.polymarket.com"
    POLYMARKET_GAMMA_URL: str = "https://gamma-api.polymarket.com"
    MARKET_POLL_INTERVAL: int = 30

    CORS_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
