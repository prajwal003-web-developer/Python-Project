
from pydantic import BaseModel, EmailStr, Field, model_validator


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def validate_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    full_name: str
    username: str
    email: EmailStr
    saved_notes: list[str] = []


class MessageResponse(BaseModel):
    message: str
    authenticated: bool
