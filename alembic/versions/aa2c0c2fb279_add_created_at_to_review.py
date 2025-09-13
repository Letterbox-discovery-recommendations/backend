"""add created_at to review

Revision ID: aa2c0c2fb279
Revises: 909ef6906900
Create Date: 2025-09-13 15:53:20.726023

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = 'aa2c0c2fb279'
down_revision = '909ef6906900'
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass