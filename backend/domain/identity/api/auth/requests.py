from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Request body for logging in with an email and password."""

    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RegisterRequest(BaseModel):
    """Request body for registering a new account."""

    display_name: str = Field(min_length=1, max_length=128)
    email: EmailStr = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)
