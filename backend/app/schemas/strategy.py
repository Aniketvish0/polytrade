import uuid
from datetime import datetime

from pydantic import BaseModel


class StrategyCreate(BaseModel):
    name: str
    rules: dict
    context: str = ""
    priority: int = 0


class StrategyUpdate(BaseModel):
    name: str | None = None
    rules: dict | None = None
    context: str | None = None
    priority: int | None = None


class StrategyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_active: bool
    priority: int
    rules: dict
    context: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
