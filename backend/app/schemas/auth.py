from pydantic import ConfigDict, EmailStr, field_validator, model_validator

from app.core.security import validate_password_strength
from app.schemas.common import CamelModel
from app.schemas.user import UserAccount, clean_name, clean_username


class RegisterRequest(CamelModel):
    # Unknown fields (e.g. a submitted "role") are ignored; role is always "user".
    model_config = ConfigDict(extra="ignore")

    name: str
    username: str
    email: EmailStr
    password: str
    confirm_password: str | None = None

    @field_validator("name")
    @classmethod
    def _name(cls, v: str) -> str:
        return clean_name(v)

    @field_validator("username")
    @classmethod
    def _username(cls, v: str) -> str:
        return clean_username(v)

    @field_validator("password")
    @classmethod
    def _password(cls, v: str) -> str:
        return validate_password_strength(v)

    @model_validator(mode="after")
    def _confirm(self) -> "RegisterRequest":
        if self.confirm_password is not None and self.confirm_password != self.password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(CamelModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def _len(cls, v: str) -> str:
        if not v or len(v) > 128:
            raise ValueError("Invalid password")
        return v


class AuthResponse(CamelModel):
    user: UserAccount
    csrf_token: str


class CsrfResponse(CamelModel):
    csrf_token: str
