"""rename_metadata_to_extra_data

Revision ID: 5d33084d072a
Revises: 758322f7a771
Create Date: 2026-03-02 04:01:29.119559

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '5d33084d072a'
down_revision: Union[str, Sequence[str], None] = '758322f7a771'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('messages', 'metadata', new_column_name='extra_data')


def downgrade() -> None:
    op.alter_column('messages', 'extra_data', new_column_name='metadata')
