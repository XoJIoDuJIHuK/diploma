from fastapi import (
    Depends,
    HTTPException,
    Path,
    status,
)

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import StylePrompt
from src.depends import get_session
from src.database.repos.prompt import PromptRepo


async def get_prompt(
    prompt_id: int = Path(),
    db_session: AsyncSession = Depends(get_session),
) -> StylePrompt:
    prompt = await PromptRepo.get_by_id(
        prompt_id=prompt_id, db_session=db_session
    )
    return prompt
