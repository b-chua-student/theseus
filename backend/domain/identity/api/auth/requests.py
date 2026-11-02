from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class RegisterRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=128)
    email: EmailStr = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=128)
