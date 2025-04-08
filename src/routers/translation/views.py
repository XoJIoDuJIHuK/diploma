from operator import mod
from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Request,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import BalanceChangeCause
from src.util.brokers.consumer.schemes import TranslationMessage
from src.database.repos.article import ArticleRepo
from src.database.repos.language import LanguageRepo
from src.database.repos.model import ModelRepo
from src.database.repos.prompt import PromptRepo
from src.database.repos.translation_task import TaskRepo
from src.database.repos.user import UserRepo
from src.depends import get_session
from src.logger import get_logger
from src.http_responses import get_responses
from src.responses import BaseResponse
from src.routers.translation.schemes import (
    CreateTaskScheme,
    CreateTranslationScheme,
    EstimationRequestScheme,
    EstimationResponseScheme,
    SimpleTranslationOutScheme,
    SimpleTranslationRequestScheme,
)
from src.settings import rabbitmq_config, simple_translation_config, Role
from src.util.auth.classes import JWTCookie
from src.util.auth.schemes import UserInfo
from src.util.common.helpers import get_ip
from src.util.storage.classes import RedisHandler
from src.util.time.helpers import get_utc_now
from src.util.translator.classes import Gpt4freeTranslator
from src.util.translator.helpers import estimate_translation_tokens
from src.util.brokers.producer.rabbitmq import publish_message

router = APIRouter(prefix='/translation', tags=['Translation'])
logger = get_logger(__name__)


@router.post('/simple/')
async def get_simple_translation(
    translation_data: SimpleTranslationRequestScheme,
    request: Request,
    db_session: AsyncSession = Depends(get_session),
    user_info: UserInfo | None = Depends(
        JWTCookie(auto_error=False, roles=[Role.user])
    ),
):
    if not simple_translation_config.is_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    redis_key = simple_translation_config.redis_cache_template.format(
        get_ip(request),
        get_utc_now().replace(minute=0, second=0, microsecond=0),
    )
    logger.info('Key to check: %s', redis_key)
    redis_handler = RedisHandler()
    used_attempts = int(await redis_handler.get(redis_key) or 0)

    source_language = await LanguageRepo.get_by_id(
        language_id=translation_data.source_language_id,
        db_session=db_session,
    )
    target_language = await LanguageRepo.get_by_id(
        language_id=translation_data.target_language_id,
        db_session=db_session,
    )
    if target_language is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Конечный язык не найден',
        )
    model = await ModelRepo.get_by_id(
        model_id=translation_data.model_id,
        db_session=db_session,
    )
    prompt = await PromptRepo.get_by_id(
        prompt_id=translation_data.prompt_id,
        db_session=db_session,
    )

    if (
        user_info is None
        and used_attempts > simple_translation_config.max_usages_per_hour
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail='Превышен лимит. Попробуйте позже',
        )
    elif user_info is not None:
        try:
            user = await UserRepo.get_by_id(
                user_id=user_info.id,
                db_session=db_session,
            )
        except HTTPException as e:
            if e.status_code == status.HTTP_404_NOT_FOUND:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail='Пользователь исчез, залогиньтесь заново',
                )
            else:
                raise e
        estimated_cost = (
            estimate_translation_tokens(
                input_text=translation_data.text,
                model=model,
                prompt=prompt,
            )
            * model.token_multiplier
        )
        if (
            used_attempts > simple_translation_config.max_usages_per_hour
            and user.balance < estimated_cost
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Недостаточно токенов',
            )

    translated_text, tokens_used = await Gpt4freeTranslator().translate(
        text=translation_data.text,
        source_language=source_language,
        target_language=target_language,
        model=model,
        prompt_object=prompt,
    )

    await redis_handler.set(redis_key, used_attempts + 1, 3600)

    if user_info is not None:
        await UserRepo.update_balance(
            user_id=user_info.id,
            delta=-1 * tokens_used,
            reason=BalanceChangeCause.translation,
            db_session=db_session,
        )
    return SimpleTranslationOutScheme(text=translated_text)


@router.post(
    '/',
    response_model=BaseResponse,
    responses=get_responses(400, 401, 403, 404),
)
async def create_translation(
    translation_data: CreateTranslationScheme,
    db_session: AsyncSession = Depends(get_session),
    user_info: UserInfo = Depends(JWTCookie(roles=[Role.user])),
):
    user = await UserRepo.get_by_id(
        user_id=user_info.id, db_session=db_session
    )
    article = await ArticleRepo.get_by_id(
        article_id=translation_data.article_id, db_session=db_session
    )
    if article.user_id != user_info.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Статья не найдена'
        )
    if article.original_article_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Нельзя переводить перевод',
        )
    model = await ModelRepo.get_by_id(
        model_id=translation_data.model_id,
        db_session=db_session,
    )
    prompt = await PromptRepo.get_by_id(
        prompt_id=translation_data.prompt_id,
        db_session=db_session,
    )
    estimated_tokens = (
        estimate_translation_tokens(
            input_text=article.text,
            model=model,
            prompt=prompt,
        )
        * len(translation_data.target_language_ids)
        * model.token_multiplier
    )
    if user.balance <= estimated_tokens:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Недостаточно токенов',
        )

    failed_languages = []
    for target_language_id in translation_data.target_language_ids:
        if not await LanguageRepo.exists(
            language_id=target_language_id, db_session=db_session
        ):
            failed_languages.append(target_language_id)
            continue
        task = await TaskRepo.create(
            task_data=CreateTaskScheme(
                article_id=translation_data.article_id,
                model_id=translation_data.model_id,
                prompt_id=translation_data.prompt_id,
                target_language_id=target_language_id,
            ),
            db_session=db_session,
        )
        message = TranslationMessage(task_id=task.id)

        await db_session.flush()
        publish_message(
            rabbitmq_config.translation_topic, message.model_dump(mode='json')
        )
    if not failed_languages:
        return BaseResponse(message='Перевод запущен. Ожидайте')
    if len(failed_languages) == len(translation_data.target_language_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Ни один из языков не поддерживается',
        )
    return BaseResponse(
        message=(
            f'Перевод запущен. Следующие языки не '
            f'поддерживаются {failed_languages}'
        )
    )


@router.get('/estimate/')
async def get_text_estimation(
    request_data: EstimationRequestScheme,
    model_id: int,
    prompt_id: int,
    db_session: AsyncSession = Depends(get_session),
):
    model = await ModelRepo.get_by_id(
        model_id=model_id,
        db_session=db_session,
    )
    prompt = await PromptRepo.get_by_id(
        prompt_id=prompt_id,
        db_session=db_session,
    )
    estimated_tokens = estimate_translation_tokens(
        input_text=request_data.text,
        model=model,
        prompt=prompt,
    )
    return EstimationResponseScheme(tokens=estimated_tokens)
