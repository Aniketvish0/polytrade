"""add user onboarding columns

Revision ID: a1b2c3d4e5f6
Revises: 8b0e06aee5ff
Create Date: 2026-04-29 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "8b0e06aee5ff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("onboarding_completed", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("users", sa.Column("onboarding_step", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("users", sa.Column("onboarding_data", postgresql.JSONB(), nullable=True))
    # Mark existing users as onboarded so they skip the flow
    op.execute("UPDATE users SET onboarding_completed = true WHERE onboarding_completed = false")


def downgrade() -> None:
    op.drop_column("users", "onboarding_data")
    op.drop_column("users", "onboarding_step")
    op.drop_column("users", "onboarding_completed")
