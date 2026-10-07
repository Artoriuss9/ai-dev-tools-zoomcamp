from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    pubg_api_key: str | None = Field(default=None, alias="PUBG_API_KEY")
    pubg_platform: str = Field(default="steam", alias="PUBG_PLATFORM")
    pubg_mode: str = Field(default="solo-fpp", alias="PUBG_MODE")
    pubg_api_base_url: str = Field(default="https://api.pubg.com", alias="PUBG_API_BASE_URL")
    pubg_api_timeout: float = Field(default=10.0, alias="PUBG_API_TIMEOUT")
    database_url: str = Field(default="sqlite:///./pubg.db", alias="DATABASE_URL")

    def validate_runtime(self) -> None:
        if not self.pubg_api_key or self.pubg_api_key == "your_api_key_here":
            raise RuntimeError("PUBG_API_KEY is missing or invalid. Set it in .env before starting the application.")
        if self.pubg_api_timeout <= 0:
            raise RuntimeError("PUBG_API_TIMEOUT must be greater than 0.")


@lru_cache
def get_settings() -> Settings:
    return Settings()
