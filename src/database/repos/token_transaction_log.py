from typing import Sequence
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import BalanceChangeCause, TransactionLog
from src.pagination import PaginationParams, paginate


class TransactionRepo:
    @staticmethod
    async def get_by_user(
        user_id: uuid.UUID,
        pagination_params: PaginationParams,
        db_session: AsyncSession,
    ) -> tuple[Sequence[TransactionLog], int]:
        query = select(TransactionLog).filter_by(user_id=user_id)
        transations, count = await paginate(
            session=db_session, statement=query, pagination=pagination_params
        )
        return transations, count

    @staticmethod
    async def create(
        user_id: uuid.UUID,
        tokens_amount: int,
        cause: BalanceChangeCause,
        db_session: AsyncSession,
    ) -> None:
        log_entry = TransactionLog(
            user_id=user_id,
            tokens_amount=tokens_amount,
            cause=cause,
        )
        db_session.add(log_entry)
        await db_session.flush()
