"""skills

Revision ID: 6987bb2955ed
Revises: a1c6579a1af8
Create Date: 2025-05-16 21:35:37.827413

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import table, column

# revision identifiers, used by Alembic.
revision: str = '6987bb2955ed'
down_revision: Union[str, None] = 'a1c6579a1af8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # Веб-разработка
    roles_table = table(
        'roles',
        column('name', sa.Text),
        column('description', sa.Text),
        column('is_core', sa.Boolean)
    )

    op.bulk_insert(
        roles_table,
        [
            {'name': 'Frontend', 'description': 'Навык', 'is_core': False},
            {'name': 'Backend', 'description': 'Навык', 'is_core': False},
            {'name': 'Fullstack разработка', 'description': 'Навык', 'is_core': False},
            
            # Мобильная разработка
            {'name': 'iOS разработка', 'description': 'Навык', 'is_core': False},
            {'name': 'Android разработка', 'description': 'Навык', 'is_core': False},
            {'name': 'Flutter', 'description': 'Навык', 'is_core': False},
            {'name': 'React Native', 'description': 'Навык', 'is_core': False},
            
            # Программирование
            {'name': 'Python', 'description': 'Навык', 'is_core': False},
            {'name': 'Java', 'description': 'Навык', 'is_core': False},
            {'name': 'C#', 'description': 'Навык', 'is_core': False},
            {'name': 'C++', 'description': 'Навык', 'is_core': False},
            {'name': 'Go', 'description': 'Навык', 'is_core': False},
            {'name': 'Rust', 'description': 'Навык', 'is_core': False},
            {'name': 'Алгоритмы и структуры данных', 'description': 'Навык', 'is_core': False},
            
            # Базы данных
            {'name': 'SQL', 'description': 'Навык', 'is_core': False},
            {'name': 'NoSQL', 'description': 'Навык', 'is_core': False},
            {'name': 'Redis', 'description': 'Навык', 'is_core': False},
            
            # DevOps и администрирование
            {'name': 'Docker', 'description': 'Навык', 'is_core': False},
            {'name': 'Kubernetes', 'description': 'Навык', 'is_core': False},
            {'name': 'AWS', 'description': 'Навык', 'is_core': False},
            {'name': 'CI/CD', 'description': 'Навык', 'is_core': False},
            {'name': 'Linux-администрирование', 'description': 'Навык', 'is_core': False},
            
            # Графический дизайн
            {'name': 'Adobe Photoshop', 'description': 'Навык', 'is_core': False},
            {'name': 'Illustrator', 'description': 'Навык', 'is_core': False},
            {'name': 'Figma', 'description': 'Навык', 'is_core': False},
            {'name': 'CorelDRAW', 'description': 'Навык', 'is_core': False},
            {'name': 'UI/UX дизайн', 'description': 'Навык', 'is_core': False},
            {'name': 'Создание логотипов', 'description': 'Навык', 'is_core': False},
            
            # 3D и анимация
            {'name': 'Blender', 'description': 'Навык', 'is_core': False},
            {'name': 'Maya', 'description': 'Навык', 'is_core': False},
            {'name': '3ds Max', 'description': 'Навык', 'is_core': False},
            {'name': 'Motion-дизайн', 'description': ' Навык', 'is_core': False},
            
            # Видео и аудио
            {'name': 'Монтаж видео', 'description': 'Навык', 'is_core': False},
            {'name': 'Обработка звука', 'description': 'Навык', 'is_core': False},
            {'name': 'Озвучка', 'description': 'Навык', 'is_core': False},
            
            # Контент и маркетинг
            {'name': 'Копирайтинг', 'description': 'Навык', 'is_core': False},
            {'name': 'Контент-маркетинг', 'description': 'Навык', 'is_core': False},
            {'name': 'Технические переводы', 'description': 'Навык', 'is_core': False},
            {'name': 'Художественные переводы', 'description': 'Навык', 'is_core': False},
        ]
    )

    op.bulk_insert(
        sa.table('order_statuses',
            sa.column('name', sa.String),
            sa.column('description', sa.Text),
        ),
        [
            {'name': 'Активный', 'description': 'Заказ открыт для откликов'},
            {'name': 'В работе', 'description': 'Исполнитель выбран'},
            {'name': 'Завершен', 'description': 'Заказ закрыт'},
        ]
    )

    op.bulk_insert(
        sa.table('categories',
            sa.column('name', sa.String(100)),
            sa.column('description', sa.Text)
        ),
        [
            {'name': 'IT', 'description': 'Информационные технологии'},
            {'name': 'Дизайн', 'description': 'Дизайн и креатив'},
            {'name': 'Маркетинг', 'description': 'Контент и маркетинг'}
        ]
    )

    users_table = table(
        'users',
        column('id', sa.Integer),
        column('role_id', sa.Integer),
        column('login', sa.String),
        column('email', sa.String),
        column('last_name', sa.String),
        column('first_name', sa.String),
        column('password', sa.String)
    )

    op.bulk_insert(
        users_table,
        [
            {
                'id': 1,
                'role_id': 1,
                'login': 'support',
                'email': 'support@support.ru',
                'last_name': 'support',
                'first_name': 'support',
                'password': '$pbkdf2-sha512$25000$BuC8935PKeXcO6f03puTEg$W2QKSBOVqu5UZ2h7m60bl4/zaGpTojNP5fFymj48k/3vENL3wVI8MF7QozAmzrgftiy.iqYOYzRIO8BM3lJ7Rg'
            }
        ]
    )

def downgrade():
    op.execute("DELETE FROM roles WHERE name IN ("
               "'Frontend', 'Backend', 'Fullstack разработка', "
               "'iOS разработка', 'Android разработка', 'Flutter', 'React Native', "
               "'Python', 'Java', 'C#', 'C++', 'Go', 'Rust', 'Алгоритмы и структуры данных', "
               "'SQL', 'NoSQL', 'Redis', "
               "'Docker', 'Kubernetes', 'AWS', 'CI/CD', 'Linux-администрирование', "
               "'Adobe Photoshop', 'Illustrator', 'Figma', 'CorelDRAW', 'UI/UX дизайн', 'Создание логотипов', "
               "'Blender', 'Maya', '3ds Max', 'Motion-дизайн', "
               "'Монтаж видео', 'Обработка звука', 'Озвучка', "
               "'Копирайтинг', 'Контент-маркетинг', 'Технические переводы', 'Художественные переводы'"
               ")")
    op.execute(
        "DELETE FROM categories WHERE name IN ('IT', 'Дизайн', 'Маркетинг')"
    )
    op.execute(
        "DELETE FROM order_statuses WHERE text IN ('Активный', 'В работе', 'Завершен')"
    )
    op.execute(
        "DELETE FROM users WHERE email IN ('support@support.ru')"
    )
