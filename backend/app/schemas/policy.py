import uuid
from datetime import datetime

from pydantic import BaseModel


class PolicyCreate(BaseModel):
    name: str
    global_rules: dict
    category_rules: dict
    confidence_rules: dict = {}
    risk_rules: dict = {}


class PolicyUpdate(BaseModel):
    name: str | None = None
    global_rules: dict | None = None
    category_rules: dict | None = None
    confidence_rules: dict | None = None
    risk_rules: dict | None = None


class PolicyResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    is_active: bool
    global_rules: dict
    category_rules: dict
    confidence_rules: dict
    risk_rules: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
