from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    shopify_shop_name: str = Field(validation_alias=AliasChoices("SHOP_NAME", "SHOPIFY_SHOP_NAME"))
    shopify_api_version: str = Field(alias="SHOPIFY_API_VERSION")
    shopify_access_token: str = Field(alias="SHOPIFY_ACCESS_TOKEN")

    gemini_api_key: str = Field(alias="GEMINI_API_KEY")
    gemini_model: str = Field(alias="GEMINI_MODEL")

    shopify_timeout_seconds: float = Field(default=20.0, alias="SHOPIFY_TIMEOUT_SECONDS")
    shopify_max_retries: int = Field(default=3, alias="SHOPIFY_MAX_RETRIES")
    shopify_backoff_seconds: float = Field(default=0.5, alias="SHOPIFY_BACKOFF_SECONDS")
    shopify_page_limit: int = Field(default=4, alias="SHOPIFY_PAGE_LIMIT")

    allowed_origins: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")
    debug_error_details: bool = Field(default=True, alias="DEBUG_ERROR_DETAILS")

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
