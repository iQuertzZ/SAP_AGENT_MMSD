from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ConnectorType(str, Enum):
    MOCK = "mock"
    ODATA = "odata"
    RFC = "rfc"


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # SAP — connector selection
    sap_connector: ConnectorType = ConnectorType.MOCK

    # SAP OData connection
    sap_odata_base_url: str = ""
    sap_odata_user: str = ""
    sap_odata_password: str = ""
    sap_client: str = "100"
    sap_language: str = "FR"
    sap_version: Literal["auto", "ecc", "s4hana"] = "auto"
    sap_verify_ssl: bool = True
    sap_timeout_connect: float = 10.0
    sap_timeout_read: float = 30.0
    sap_max_retries: int = 3
    sap_retry_backoff: float = 1.0

    # SAP OAuth2 (S/4HANA Cloud)
    sap_oauth_url: str = ""
    sap_oauth_client_id: str = ""
    sap_oauth_client_secret: str = ""
    sap_oauth_scope: str = ""

    # SAP RFC (legacy)
    sap_rfc_host: str = ""
    sap_rfc_sysnr: str = "00"
    sap_rfc_client: str = "100"
    sap_rfc_user: str = ""
    sap_rfc_password: str = ""

    # Circuit breaker
    sap_cb_failure_threshold: int = 5
    sap_cb_recovery_timeout: int = 60

    # SAP Sandbox (API Business Hub)
    sap_sandbox: bool = False
    sap_sandbox_api_key: str = ""

    # App
    app_env: Environment = Environment.DEVELOPMENT
    app_version: str = "1.0.0"  # overridden by APP_VERSION env var (set by Docker build)
    git_sha: str = "unknown"    # overridden by GIT_SHA env var (set by Docker build)
    log_level: str = "INFO"
    secret_key: str = "dev-secret-change-in-production-min-32-chars!!"
    execution_enabled: bool = False

    # JWT
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    # First admin seed (created on startup if no admin exists)
    first_admin_email: str = "admin@sap-copilot.local"
    first_admin_password: str = "changeme"

    # Database
    database_url: str = ""
    test_database_url: str = ""
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("anthropic_api_key")
    @classmethod
    def warn_missing_key(cls, v: str) -> str:
        if not v:
            import warnings
            warnings.warn(
                "ANTHROPIC_API_KEY not set — AI analysis will use rule-based fallback",
                stacklevel=2,
            )
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == Environment.PRODUCTION

    @property
    def ai_enabled(self) -> bool:
        return bool(self.anthropic_api_key)

    @property
    def sap_use_oauth(self) -> bool:
        return bool(self.sap_oauth_url and self.sap_oauth_client_id)


settings = Settings()
