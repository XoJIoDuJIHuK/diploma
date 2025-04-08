import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
    Query,
)

from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.depends import get_session
from src.http_responses import get_responses
from src.pagination import PaginationParams, get_pagination_params
from src.responses import DataResponse, ListResponse
from src.routers.articles.schemes import (
    ArticleOutScheme,
    CreateArticleScheme,
    EditArticleScheme,
    UploadArticleScheme,
    ArticleListItemScheme,
    ArticleUpdateLikeScheme,
)
from src.database.repos.article import ArticleRepo
from src.database.repos.report import ReportRepo
from src.settings import Role
from src.util.auth.classes import JWTCookie
from src.util.auth.schemes import UserInfo

router = APIRouter(prefix='/articles', tags=['Articles'])
article_not_found_error = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail='Статья не найдена'
)


@router.get(
    '/',
    response_model=ListResponse[ArticleListItemScheme],
    responses=get_responses(400, 401, 403, 500),
)
async def get_list(
    original_article_id: uuid.UUID | None = Query(None),
    user_info: UserInfo = Depends(JWTCookie(roles=[Role.user])),
    pagination: PaginationParams = Depends(get_pagination_params),
    db_session: AsyncSession = Depends(get_session),
):
    articles, count = await ArticleRepo.get_list(
        original_article_id=original_article_id,
        user_id=user_info.id,
        pagination_params=pagination,
        db_session=db_session,
    )
    return ListResponse[ArticleListItemScheme].from_list(
        items=articles, total_count=count, params=pagination
    )


@router.get(
    '/{article_id}/',
    response_model=DataResponse.single_by_key('article', ArticleOutScheme),
    responses=get_responses(400, 401, 403),
)
async def get_article(
    article_id: uuid.UUID = Path(),
    user_info: UserInfo = Depends(JWTCookie(roles=[Role.user])),
    db_session: AsyncSession = Depends(get_session),
):
    article = await ArticleRepo.get_by_id(
        article_id=article_id,
        db_session=db_session,
    )
    if article.user_id != user_info.id:
        raise article_not_found_error
    report_exists = bool(
        await ReportRepo.get_by_article_id(
            article_id=article_id, db_session=db_session
        )
    )
    article_scheme = ArticleOutScheme.create(article, report_exists)
    return DataResponse(data={'article': article_scheme})


@router.post(
    '/',
    response_model=DataResponse.single_by_key('article', ArticleOutScheme),
    responses=get_responses(400, 401, 403, 500),
)
async def upload_article(
    article_data: UploadArticleScheme,
    user_info: UserInfo = Depends(JWTCookie(roles=[Role.user])),
    db_session: AsyncSession = Depends(get_session),
):
    article = await ArticleRepo.create(
        article_data=CreateArticleScheme(
            title=article_data.title,
            text=article_data.text,
            language_id=article_data.language_id,
            user_id=user_info.id,
        ),
        db_session=db_session,
    )
    return DataResponse(
        data={'article': ArticleOutScheme.model_validate(article)}
    )


@router.put(
    '/{article_id}/',
    response_model=DataResponse.single_by_key('article', ArticleOutScheme),
    responses=get_responses(400, 401, 403, 404, 500),
)
async def update_article(
    new_article_data: EditArticleScheme,
    article_id: uuid.UUID = Path(),
    user_info: UserInfo = Depends(JWTCookie(roles=[Role.user])),
    db_session: AsyncSession = Depends(get_session),
):
    article = await ArticleRepo.get_by_id(article_id, db_session)
    if (
        article.user_id != user_info.id
        or article.original_article_id is not None
    ):
        raise article_not_found_error
    if new_article_data.title is not None:
        article.title = new_article_data.title
    if new_article_data.text is not None:
        article.text = new_article_data.text
    db_session.add(article)
    await db_session.refresh(article)
    return DataResponse(
        data={'article': ArticleOutScheme.model_validate(article)}
    )




@router.delete(
    '/{article_id}/', responses=get_responses(400, 401, 403, 404, 500)
)
async def delete_article(
    article_id: uuid.UUID = Path(),
    user_info: UserInfo = Depends(JWTCookie(roles=[Role.user])),
    db_session: AsyncSession = Depends(get_session),
):
    article = await ArticleRepo.get_by_id(article_id, db_session)
    if article.user_id != user_info.id:
        raise article_not_found_error
    article = await ArticleRepo.delete(article=article, db_session=db_session)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={'message': f'Статья {article_id} удалена'},
    )
    # return DataResponse(
    #     data={'article': ArticleOutScheme.model_validate(article)}
    # )
