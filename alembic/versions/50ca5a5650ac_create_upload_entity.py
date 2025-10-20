"""create upload entity

Revision ID: 50ca5a5650ac
Revises: 
Create Date: 2025-10-20 11:30:12.331619

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '50ca5a5650ac'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'uploaded_files',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('filetype', sa.Enum('markdown', 'image', 'document', name='filetypeenum'), nullable=False)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('uploaded_files')
    op.execute('DROP TYPE IF EXISTS filetypeenum')
