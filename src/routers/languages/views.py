from fastapi import (
    APIRouter,
    Depends
)

from src.depends import get_session
from src.responses import SimpleListResponse
from src.routers.languages.schemes import LanguageOutScheme

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repos.language import LanguageRepo

router = APIRouter(
    prefix='/languages',
    tags=['Languages']
)


@router.get(
    '/',
    response_model=SimpleListResponse[LanguageOutScheme]
)
async def get_languages(
        db_session: AsyncSession = Depends(get_session)
):
    return SimpleListResponse[LanguageOutScheme].from_list(
        items=await LanguageRepo.get_list(db_session)
    )
