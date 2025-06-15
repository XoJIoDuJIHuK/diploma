import io
from urllib.parse import quote
import uuid

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    status,
    Query,
)
from fastapi.responses import JSONResponse, StreamingResponse

from markdown import Markdown

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
)
from src.database.repos.article import ArticleRepo
from src.database.repos.report import ReportRepo
from src.settings import Role
from src.util.auth.classes import JWTCookie
from src.util.auth.schemes import UserInfo

from weasyprint import HTML

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


@router.get('/{article_id}/download/')
async def download_article(
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
    try:
        md = Markdown(
            extensions=[
                'markdown.extensions.extra',  # includes tables, fenced_code, footnotes…
                'markdown.extensions.codehilite',  # highlight code blocks
            ]
        )

        html_content = md.convert(article.text)

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 40px;
                }}
                code {{
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                }}
                pre {{
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 3px;
                    overflow-x: auto;
                }}
                blockquote {{
                    border-left: 4px solid #ddd;
                    padding-left: 15px;
                    color: #555;
                }}
                table {{
                    border-collapse: collapse;
                    width: 100%;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 8px;
                }}
                th {{
                    background-color: #f2f2f2;
                }}
            </style>
            <title>{article.title}</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        pdf_bytes = HTML(string=full_html).write_pdf()
        assert pdf_bytes is not None

        raw_filename = (
            f'{article.title.replace(" ", "_")}-'
            + (
                article.language.iso_code
                if article.language_id is not None
                else 'NULL'
            )
            + '.pdf'
        )

        # quote(...) will percent‐encode any non‐ASCII character:
        quoted = quote(
            raw_filename, safe=''
        )  # “safe=” means everything outside A-Z a-z 0-9 gets %XX-encoded
        # Use RFC 5987 syntax in the header
        content_disposition = f"attachment; filename*=UTF-8''{quoted}"

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type='application/pdf',
            headers={
                'Content-Disposition': content_disposition,
                'Content-Length': str(len(pdf_bytes)),
            },
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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
    await db_session.flush()
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
