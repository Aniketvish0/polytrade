import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    email: str
    password: str
    display_name: str | None = None
    initial_balance: Decimal = Decimal("1000.00")


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    display_name: str | None
    role: str
    initial_balance: Decimal
    is_active: bool
    onboarding_completed: bool = False
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
