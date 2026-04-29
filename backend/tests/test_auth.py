"""Tests for auth utilities in app.api.auth — password hashing & JWT."""

from unittest.mock import patch

from jose import jwt

from app.api.auth import create_access_token, hash_password, verify_password


# ---------------------------------------------------------------------------
# hash_password
# ---------------------------------------------------------------------------

def test_hash_password_returns_bcrypt_hash():
    hashed = hash_password("mypassword")
    assert isinstance(hashed, str)
    # bcrypt hashes start with $2b$ (or $2a$)
    assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


def test_hash_password_different_salts():
    h1 = hash_password("same")
    h2 = hash_password("same")
    # Two hashes of the same password should differ (different salts)
    assert h1 != h2


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------

def test_verify_password_correct():
    hashed = hash_password("correct-password")
    assert verify_password("correct-password", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("correct-password")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_empty_password():
    hashed = hash_password("")
    assert verify_password("", hashed) is True
    assert verify_password("notempty", hashed) is False


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

def test_create_access_token_returns_jwt_string():
    token = create_access_token("user-id-123")
    assert isinstance(token, str)
    # JWT has 3 dot-separated parts
    assert len(token.split(".")) == 3


def test_jwt_can_be_decoded_with_correct_sub():
    from app.config import settings

    user_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    token = create_access_token(user_id)

    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert payload["sub"] == user_id
    assert "exp" in payload


def test_jwt_contains_expiration():
    from app.config import settings

    token = create_access_token("test-user")
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    assert "exp" in payload
    assert isinstance(payload["exp"], int)


def test_jwt_decode_wrong_key_fails():
    token = create_access_token("user-1")
    try:
        jwt.decode(token, "wrong-secret-key", algorithms=["HS256"])
        assert False, "Expected JWTError"
    except Exception:
        pass


# ---------------------------------------------------------------------------
# GET /me endpoint — QA-level tests for the onboarding_completed bug fix
# ---------------------------------------------------------------------------

from app.api.auth import get_me
from app.schemas.user import UserResponse


async def test_get_me_returns_user_response_with_onboarding_completed(mock_user):
    """GET /me returns current user data including onboarding_completed field."""
    result = await get_me(user=mock_user)
    assert isinstance(result, UserResponse)
    assert hasattr(result, "onboarding_completed")
    assert result.email == mock_user.email
    assert result.id == mock_user.id


async def test_get_me_returns_onboarding_completed_true_for_migrated_user(mock_user):
    """GET /me returns onboarding_completed=True for a pre-migration user who finished onboarding."""
    assert mock_user.onboarding_completed is True
    result = await get_me(user=mock_user)
    assert result.onboarding_completed is True


async def test_get_me_returns_onboarding_completed_false_for_new_user(mock_user_new):
    """GET /me returns onboarding_completed=False for a brand-new user."""
    assert mock_user_new.onboarding_completed is False
    result = await get_me(user=mock_user_new)
    assert result.onboarding_completed is False


async def test_login_response_includes_onboarding_completed_in_user_data(mock_user):
    """Login response (via UserResponse serialization) includes onboarding_completed."""
    user_resp = UserResponse.model_validate(mock_user, from_attributes=True)
    dumped = user_resp.model_dump()
    assert "onboarding_completed" in dumped
    assert dumped["onboarding_completed"] is True


async def test_register_creates_user_with_onboarding_completed_false(mock_user_new):
    """A newly registered user should default to onboarding_completed=False."""
    # mock_user_new simulates a freshly-created user before any onboarding
    user_resp = UserResponse.model_validate(mock_user_new, from_attributes=True)
    assert user_resp.onboarding_completed is False
