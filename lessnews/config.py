from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    debug: bool = Field(default=False)
    cache_path: str = Field(default="./cache")
    cache_cron_minutes: int = Field(default=15)  # Every 15 minutes
    cache_max_hours: int = Field(default=168)  # 7 days
    port: int = Field(default=8001)
    host: str = Field(default="127.0.0.1")

    model_config = SettingsConfigDict(env_prefix="LESSNEWS_")
