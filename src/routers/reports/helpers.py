import uuid
from typing import Callable, Any, Coroutine

from fastapi import (
    Depends,
    HTTPException,
    Path,
    status,
)

from src.depends import get_session
from src.database.models import Report
from src.database.repos.article import ArticleRepo
from src.settings import Role
from src.util.auth.classes import JWTCookie
from src.util.auth.schemes import UserInfo

from sqlalchemy.ext.asyncio import AsyncSession


def get_report(
    owner_only: bool = True,
) -> Callable[[], Coroutine[Any, Any, Report | None]]:
    async def async_function(
        article_id: uuid.UUID = Path(),
        db_session: AsyncSession = Depends(get_session),
        user_info: UserInfo = Depends(
            JWTCookie(roles=[Role.user, Role.moderator])
        ),
    ) -> Report | None:
        article = await ArticleRepo.get_by_id(
            article_id=article_id,
            db_session=db_session,
        )
        if (
            article.user_id != user_info.id
            and user_info.role != Role.moderator
            and not owner_only
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Статья не найдена',
            )
        return article.report

    return async_function
