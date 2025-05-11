"""add_initial_roles

Revision ID: dfa455c2bdec
Revises: 9a4fc5eeb8cd
Create Date: 2025-05-11 14:18:08.444332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm import Session

from models import Roles

# revision identifiers, used by Alembic.
revision: str = 'dfa455c2bdec'
down_revision: Union[str, None] = '9a4fc5eeb8cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        roles = [
            Roles(name='admin', description='Администратор системы с полными правами'),
            Roles(name='manager', description='Менеджер с ограниченными правами администрирования'),
            Roles(name='user', description='Обычный пользователь с базовыми правами'),
            Roles(name='guest', description='Гостевой аккаунт с минимальными правами')
        ]

        session.add_all(roles)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def downgrade():
    op.execute("DELETE FROM roles WHERE name IN ('admin', 'manager', 'user', 'guest')")
