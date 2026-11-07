from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """UZMEGATV Bot configuration settings loaded from environment or .env file."""

    BOT_TOKEN: str = "DEFAULT_TOKEN"
    BOT_USERNAME: str = "uz_megatv_bot"
    ADMIN_IDS: Union[str, List[int]] = []
    ADMIN_USERNAMES: Union[str, List[str]] = ["abdurahimoovvvv"]
    DATABASE_URL: str = "sqlite+aiosqlite:///uzmegatv.db"
    REDIS_URL: Optional[str] = None
    THROTTLE_RATE: float = 0.7
    ITEMS_PER_PAGE: int = 6
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, List[int], int]) -> List[int]:
        if isinstance(v, int):
            return [v]
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return []

    @field_validator("ADMIN_USERNAMES", mode="before")
    @classmethod
    def parse_admin_usernames(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, list):
            return [x.strip().lower().lstrip("@") for x in v if x]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            return [x.strip().lower().lstrip("@") for x in v.split(",") if x.strip()]
        return []

    def is_admin(self, user_id: int, username: Optional[str] = None) -> bool:
        """Check whether user_id or username belongs to the admin list."""
        if user_id in self.ADMIN_IDS:
            return True
        if username and username.strip().lower().lstrip("@") in self.ADMIN_USERNAMES:
            return True
        return False


settings = Settings()
