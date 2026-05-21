from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    user_id: str
    email: str
    display_name: str | None = None
    access_token: str
    token_type: str = 'bearer'


class UserMeResponse(BaseModel):
    user_id: str
    email: str
    display_name: str | None = None
