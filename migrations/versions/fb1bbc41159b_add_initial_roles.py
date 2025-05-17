"""add_initial_roles

Revision ID: fb1bbc41159b
Revises: 9a1f4ea60bed
Create Date: 2025-05-12 21:04:42.312174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column

# revision identifiers, used by Alembic.
revision: str = 'fb1bbc41159b'
down_revision: Union[str, None] = '9a1f4ea60bed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Определяем структуру таблицы для вставки данных
    roles_table = table(
        'roles',
        column('name', sa.String(50)),
        column('description', sa.String(300))
    )

    # Вставляем начальные роли
    op.bulk_insert(
        roles_table,
        [
            {
                'name': 'admin',
                'description': 'Роль'
            },
            {
                'name': 'manager',
                'description': 'Роль'
            },
            {
                'name': 'user',
                'description': 'Роль'
            },
            {
                'name': 'guest',
                'description': 'Роль'
            }
        ]
    )


def downgrade():
    # Удаляем добавленные роли (по именам для безопасности)
    op.execute(
        "DELETE FROM roles WHERE name IN ('admin', 'manager', 'user', 'guest')"
    )

