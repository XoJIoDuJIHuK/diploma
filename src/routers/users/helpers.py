import uuid

from fastapi import (
    Depends,
    Path,
)

from src.database.models import User
from src.database.repos.user import UserRepo
from src.depends import get_session

from sqlalchemy.ext.asyncio import AsyncSession


async def get_user(
    db_session: AsyncSession = Depends(get_session),
    user_id: uuid.UUID = Path(),
) -> User:
    return await UserRepo.get_by_id(user_id, db_session)
