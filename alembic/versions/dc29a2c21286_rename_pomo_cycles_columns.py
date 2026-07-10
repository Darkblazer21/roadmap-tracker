"""rename pomo cycles columns

Revision ID: dc29a2c21286
Revises: 5845a03ee9f7
Create Date: 2026-07-10 15:01:13.940786
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'dc29a2c21286'
down_revision: Union[str, Sequence[str], None] = '5845a03ee9f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "app_settings",
        "pomo_cycles_per_short_set",
        new_column_name="pomo_cycles_per_set",
    )
    op.alter_column(
        "app_settings",
        "pomo_cycles_per_long_break",
        new_column_name="pomo_cycles_per_marathon",
    )


def downgrade() -> None:
    op.alter_column(
        "app_settings",
        "pomo_cycles_per_marathon",
        new_column_name="pomo_cycles_per_long_break",
    )
    op.alter_column(
        "app_settings",
        "pomo_cycles_per_set",
        new_column_name="pomo_cycles_per_short_set",
    )