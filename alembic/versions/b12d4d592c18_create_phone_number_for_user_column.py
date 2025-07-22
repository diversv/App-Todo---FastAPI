"""Create phone number for user column

Revision ID: b12d4d592c18
Revises: 
Create Date: 2025-07-21 21:44:54.473737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b12d4d592c18'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('phone_number', sa.String, nullable = True))


def downgrade() -> None:
    op.drop_column('users', 'phone_number')