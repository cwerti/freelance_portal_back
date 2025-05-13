import contextlib
from contextvars import ContextVar
from typing import Tuple, Callable, ContextManager, Generator, AsyncGenerator, AsyncContextManager, Union

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool

session_context: ContextVar[Union[AsyncSession, Session]] = ContextVar("session_context")

async_engine_default_params = {"poolclass": NullPool}


def async_session_factory(
    async_connection_string, **engine_params
) -> Tuple[AsyncGenerator[AsyncSession, None], Callable[[], AsyncContextManager[AsyncSession]], AsyncEngine]:
    """
    Функция для создания асинхронной фабрики соединений с бд

    :param async_connection_string: connection url начинающийся с postgresql+asyncpg
    :param engine_params: параметры для AsyncEngine (настройки пула соединений)
    :return: генератор для использования в fastapi.Depends, контекстный менеджер
             бд для использования в любом ином месте, AsyncEngine для низкоуровнего взаимодействия
    """
    params = async_engine_default_params.copy()
    params.update(engine_params)

    engine = create_async_engine(async_connection_string, **params)
    # noinspection PyTypeChecker
    maker = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async def get_async_session() -> AsyncSession:
        try:
            sess: AsyncSession = maker()
            session_context.set(sess)
            yield sess
        except Exception as e:
            await sess.rollback()
            raise e
        finally:
            await sess.commit()
            await sess.close()

    return get_async_session, contextlib.asynccontextmanager(get_async_session), engine


def session_factory(
    connection_string, **engine_params
) -> Tuple[Generator[Session, None, None], Callable[[], ContextManager[Session]], Engine]:
    """
    Функция для создания фабрики соединений с бд

    :param async_connection_string: connection url
    :param engine_params: параметры для Engine (настройки пула соединений)
    :return: генератор для использования в fastapi.Depends, контекстный менеджер
             бд для использования в любом ином месте, Engine для низкоуровнего взаимодействия
    """
    engine = create_engine(connection_string, **engine_params)
    Session = sessionmaker(bind=engine)

    def get_session() -> Generator[Session, None, None]:
        try:
            sess: Session = Session()
            session_context.set(sess)
            yield sess
        except Exception as e:
            sess.rollback()
            raise e
        finally:
            sess.commit()
            sess.close()

    return get_session, contextlib.contextmanager(get_session), engine
