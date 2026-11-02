"""Application configuration – environment driven."""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenRouter
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(
        "https://openrouter.ai/api/v1", alias="OPENROUTER_BASE_URL"
    )
    openrouter_scope_model: str = Field(
        "meta-llama/llama-3.1-70b-instruct", alias="OPENROUTER_SCOPE_MODEL"
    )
    openrouter_verifier_model: str = Field(
        "mistralai/mistral-large", alias="OPENROUTER_VERIFIER_MODEL"
    )

    # Database
    database_url: str = Field(
        "postgresql+asyncpg://scopepilot:scopepilot@localhost:5432/scopepilot",
        alias="DATABASE_URL",
    )
    database_echo: bool = Field(False, alias="DATABASE_ECHO")

    # Application
    app_env: str = Field("development", alias="APP_ENV")
    app_debug: bool = Field(True, alias="APP_DEBUG")
    secret_key: str = Field("change-me", alias="SECRET_KEY")
    api_prefix: str = Field("/api/v1", alias="API_PREFIX")

    # Zoho
    zoho_salesiq_webhook_secret: Optional[str] = Field(None, alias="ZOHO_SALESIQ_WEBHOOK_SECRET")
    zoho_salesiq_api_key: Optional[str] = Field(None, alias="ZOHO_SALESIQ_API_KEY")
    zoho_salesiq_org_id: Optional[str] = Field(None, alias="ZOHO_SALESIQ_ORG_ID")

    zoho_cliq_webhook_secret: Optional[str] = Field(None, alias="ZOHO_CLIQ_WEBHOOK_SECRET")
    zoho_cliq_bot_token: Optional[str] = Field(None, alias="ZOHO_CLIQ_BOT_TOKEN")
    zoho_cliq_channel_id: Optional[str] = Field(None, alias="ZOHO_CLIQ_CHANNEL_ID")
    zoho_cliq_approval_webhook_url: Optional[str] = Field(
        None, alias="ZOHO_CLIQ_APPROVAL_WEBHOOK_URL"
    )

    # MCP
    mcp_host: str = Field("0.0.0.0", alias="MCP_HOST")
    mcp_port: int = Field(8001, alias="MCP_PORT")

    # Estimation
    default_hourly_rate: float = Field(75.0, alias="DEFAULT_HOURLY_RATE")
    default_currency: str = Field("USD", alias="DEFAULT_CURRENCY")

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
