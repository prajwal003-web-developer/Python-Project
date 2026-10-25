from functools import lru_cache
from typing import Literal

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # App
    app_name: str = "ADTU Notes API"
    environment: Literal["development", "testing", "production"] = "development"
    enable_docs: bool = True
    api_prefix: str = "/api"
    frontend_origins: str = "http://localhost:5173"

    # MongoDB
    mongodb_url: SecretStr
    mongodb_db_name: str = "adtu_notes"

    # JWT / cookies
    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    cookie_secure: bool | None = None
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None

    # Cloudinary
    cloudinary_cloud_name: str = ""
    cloudinary_api_key: str = ""
    cloudinary_api_secret: SecretStr = SecretStr("")
    cloudinary_folder: str = "adtu-notes/notes"
    max_upload_size_mb: int = 10
    max_semesters: int = 8

    # Abuse protection
    rate_limit_enabled: bool = True
    trust_proxy_headers: bool = False
    login_rate_limit: int = 10
    login_rate_window_seconds: int = 900
    register_rate_limit: int = 5
    register_rate_window_seconds: int = 3600
    refresh_rate_limit: int = 30
    refresh_rate_window_seconds: int = 300
    upload_rate_limit: int = 30
    upload_rate_window_seconds: int = 3600
    department_request_rate_limit: int = 10
    department_request_rate_window_seconds: int = 3600

    @field_validator("cookie_secure", "cookie_domain", mode="before")
    @classmethod
    def _blank_to_none(cls, v):
        return None if isinstance(v, str) and v.strip() == "" else v

    @field_validator("jwt_secret_key")
    @classmethod
    def _secret_length(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
        return v

    @model_validator(mode="after")
    def _cross_checks(self) -> "Settings":
        if "*" in self.cors_origins:
            raise ValueError("FRONTEND_ORIGINS must list exact origins, not '*', when using cookies")
        if self.cookie_samesite == "none" and not self.use_secure_cookies:
            raise ValueError("COOKIE_SAMESITE=none requires secure cookies")
        if self.is_production:
            if self.jwt_secret_key.get_secret_value().startswith("replace-with"):
                raise ValueError("Replace the placeholder JWT_SECRET_KEY before running in production")
            if not self.use_secure_cookies:
                raise ValueError("Secure cookies are required in production")
        return self

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def use_secure_cookies(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip().rstrip("/") for o in self.frontend_origins.split(",") if o.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
