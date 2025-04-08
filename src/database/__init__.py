import asyncio
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator

from fastapi import HTTPException

from src.settings import database_config, LOGGER_PREFIX
from src.logger import get_logger

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

async_engine = create_async_engine(
    database_config.url,
    # echo=True,
)
AsyncDBSession = async_sessionmaker(async_engine)


logger = get_logger(LOGGER_PREFIX + __name__)
semaphore = asyncio.Semaphore(5)


class Base(DeclarativeBase):
    pass


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with semaphore:
        async with AsyncDBSession() as session:
            try:
                yield session
            except HTTPException as e:
                await session.rollback()
                raise e
            except Exception as e:
                logger.warning('Session rollback because of exception: %s', e)
                await session.rollback()
                raise e
            else:
                logger.info('Committing session')
                await session.commit()
            finally:
                await session.close()
