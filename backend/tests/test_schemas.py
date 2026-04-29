"""Tests for app.schemas.user — Pydantic schemas."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

from app.schemas.user import TokenResponse, UserRegister, UserResponse


# ---------------------------------------------------------------------------
# UserResponse
# ---------------------------------------------------------------------------

def test_user_response_from_attributes():
    """UserResponse should populate from an ORM-like object via from_attributes."""
    obj = MagicMock()
    obj.id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    obj.email = "user@example.com"
    obj.display_name = "Test User"
    obj.role = "owner"
    obj.initial_balance = Decimal("1000.00")
    obj.is_active = True
    obj.onboarding_completed = True
    obj.created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)

    resp = UserResponse.model_validate(obj, from_attributes=True)
    assert resp.id == obj.id
    assert resp.email == "user@example.com"
    assert resp.display_name == "Test User"
    assert resp.role == "owner"
    assert resp.initial_balance == Decimal("1000.00")
    assert resp.is_active is True
    assert resp.created_at == datetime(2025, 1, 1, tzinfo=timezone.utc)


def test_user_response_includes_onboarding_completed():
    obj = MagicMock()
    obj.id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    obj.email = "user@example.com"
    obj.display_name = None
    obj.role = "owner"
    obj.initial_balance = Decimal("1000.00")
    obj.is_active = True
    obj.onboarding_completed = False
    obj.created_at = datetime(2025, 6, 1, tzinfo=timezone.utc)

    resp = UserResponse.model_validate(obj, from_attributes=True)
    assert resp.onboarding_completed is False


def test_user_response_onboarding_completed_default():
    """If the source object doesn't supply onboarding_completed, it defaults to False."""
    data = {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "email": "user@example.com",
        "display_name": None,
        "role": "owner",
        "initial_balance": Decimal("1000.00"),
        "is_active": True,
        "created_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
    }
    resp = UserResponse(**data)
    assert resp.onboarding_completed is False


def test_user_response_display_name_nullable():
    data = {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "email": "user@example.com",
        "display_name": None,
        "role": "owner",
        "initial_balance": Decimal("500.00"),
        "is_active": True,
        "onboarding_completed": True,
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    resp = UserResponse(**data)
    assert resp.display_name is None


def test_user_response_serialisation_roundtrip():
    data = {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "email": "user@example.com",
        "display_name": "User",
        "role": "owner",
        "initial_balance": Decimal("1000.00"),
        "is_active": True,
        "onboarding_completed": True,
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    resp = UserResponse(**data)
    dumped = resp.model_dump()
    assert dumped["email"] == "user@example.com"
    assert dumped["onboarding_completed"] is True
    assert isinstance(dumped["id"], uuid.UUID)


# ---------------------------------------------------------------------------
# UserRegister
# ---------------------------------------------------------------------------

def test_user_register_defaults():
    reg = UserRegister(email="new@example.com", password="secret")
    assert reg.email == "new@example.com"
    assert reg.password == "secret"
    assert reg.display_name is None
    assert reg.initial_balance == Decimal("1000.00")


def test_user_register_custom_values():
    reg = UserRegister(
        email="custom@example.com",
        password="pwd123",
        display_name="Custom User",
        initial_balance=Decimal("5000.00"),
    )
    assert reg.display_name == "Custom User"
    assert reg.initial_balance == Decimal("5000.00")


# ---------------------------------------------------------------------------
# TokenResponse
# ---------------------------------------------------------------------------

def test_token_response_structure():
    user_data = {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "email": "user@example.com",
        "display_name": None,
        "role": "owner",
        "initial_balance": Decimal("1000.00"),
        "is_active": True,
        "onboarding_completed": False,
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    user_resp = UserResponse(**user_data)
    token = TokenResponse(access_token="jwt.token.here", user=user_resp)

    assert token.access_token == "jwt.token.here"
    assert token.token_type == "bearer"
    assert token.user.email == "user@example.com"


def test_token_response_default_token_type():
    user_data = {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "email": "u@ex.com",
        "display_name": None,
        "role": "owner",
        "initial_balance": Decimal("1000.00"),
        "is_active": True,
        "onboarding_completed": False,
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
    }
    token = TokenResponse(access_token="abc", user=UserResponse(**user_data))
    assert token.token_type == "bearer"


# ---------------------------------------------------------------------------
# QA-level tests — serialization roundtrip & default behavior
# ---------------------------------------------------------------------------


def test_user_response_serialization_roundtrip_preserves_onboarding_completed_false():
    """Verify False is not dropped during serialization (important: schema defaults to False)."""
    data = {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "email": "roundtrip@example.com",
        "display_name": "Roundtrip User",
        "role": "owner",
        "initial_balance": Decimal("1000.00"),
        "is_active": True,
        "onboarding_completed": False,
        "created_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
    }
    resp = UserResponse(**data)

    # Serialize to dict
    dumped = resp.model_dump()
    assert "onboarding_completed" in dumped
    assert dumped["onboarding_completed"] is False

    # Serialize to JSON and back
    json_str = resp.model_dump_json()
    assert '"onboarding_completed":false' in json_str.replace(" ", "")

    # Reconstruct from JSON dict — field must survive the round trip
    restored = UserResponse.model_validate(dumped)
    assert restored.onboarding_completed is False


def test_user_response_from_user_missing_onboarding_completed_defaults_correctly():
    """When source data has no onboarding_completed, the default (False) is used."""
    data = {
        "id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "email": "missing-field@example.com",
        "display_name": None,
        "role": "owner",
        "initial_balance": Decimal("500.00"),
        "is_active": True,
        # onboarding_completed intentionally omitted
        "created_at": datetime(2025, 6, 1, tzinfo=timezone.utc),
    }
    resp = UserResponse(**data)
    assert resp.onboarding_completed is False

    # Also check it ends up in serialized output
    dumped = resp.model_dump()
    assert dumped["onboarding_completed"] is False
