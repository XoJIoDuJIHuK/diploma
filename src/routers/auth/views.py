import time

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)

from pydantic import EmailStr
from starlette.responses import JSONResponse

from src.util.brokers.producer.rabbitmq import publish_message
from src.database.models import ConfirmationType
from src.depends import get_session
from src.http_responses import get_responses
from src.responses import BaseResponse
from src.routers.auth.schemes import RegistrationScheme, ResetPasswordScheme
from src.routers.users.schemes import CreateUserScheme
from src.database.repos.confirmation_code import ConfirmationCodeRepo
from src.database.repos.session import SessionRepo
from src.database.repos.user import UserRepo
from src.settings import (
    app_config,
    Role,
    unisender_config,
    jwt_config,
    front_config,
    rabbitmq_config,
)
from src.util.auth.classes import AuthHandler, JWTCookie
from src.util.auth.helpers import (
    get_password_hash,
    get_user_agent,
    get_authenticated_response,
    send_email_confirmation_message,
)
from src.util.auth.schemes import LoginScheme, UserInfo

from sqlalchemy.ext.asyncio import AsyncSession

from src.util.mail.schemes import SendEmailScheme
from src.util.common.helpers import get_ip

from urllib.parse import urlencode, urljoin

router = APIRouter(prefix='/auth', tags=['Auth'])


@router.post('/login/', responses=get_responses(404))
async def login(
    login_data: LoginScheme,
    request: Request,
    db_session: AsyncSession = Depends(get_session),
):
    user = await UserRepo.get_by_email(
        email=login_data.email, db_session=db_session
    )
    if not user or user.password_hash != get_password_hash(
        login_data.password
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Неправильные данные для входа',
        )
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Подтвердите адрес электронной почты',
        )
    if app_config.close_sessions_on_same_device_login:
        await SessionRepo.close_all(
            user_id=user.id,
            ip=get_ip(request),
            user_agent=get_user_agent(request),
            db_session=db_session,
        )
    await db_session.refresh(user)
    tokens = await AuthHandler.login(
        user=user, request=request, db_session=db_session
    )
    response = JSONResponse({'detail': 'Аутентифицирован'})
    return get_authenticated_response(response, tokens)


@router.post(
    '/register/', response_model=BaseResponse, responses=get_responses(409)
)
async def register(
    registration_data: RegistrationScheme,
    db_session: AsyncSession = Depends(get_session),
):
    if await UserRepo.name_is_taken(
        name=registration_data.name, db_session=db_session
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail='Имя занято'
        )
    user = await UserRepo.create(
        user_data=CreateUserScheme(
            name=registration_data.name,
            email=registration_data.email,
            email_verified=False,
            password=registration_data.password,
            role=Role.user,
            balance=0,
        ),
        db_session=db_session,
    )
    await send_email_confirmation_message(
        user=user, email=registration_data.email, db_session=db_session
    )
    return BaseResponse(message='Регистрация успешна. Проверьте почту')


@router.post('/confirm-email/request/')
async def request_email_confirmation(
    email: EmailStr,
    db_session: AsyncSession = Depends(get_session),
):
    user = await UserRepo.get_by_email(email=email, db_session=db_session)
    if not user or user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден',
        )
    await send_email_confirmation_message(
        user=user, email=email, db_session=db_session
    )
    return BaseResponse(message='Проверьте почту')


@router.post(
    '/registration/confirm/',
    response_model=BaseResponse,
    responses=get_responses(400, 404),
)
async def confirm_email(
    code: str,
    db_session: AsyncSession = Depends(get_session),
):
    confirmation_code = await ConfirmationCodeRepo.get(
        value=code, reason=ConfirmationType.registration, db_session=db_session
    )
    if not confirmation_code or confirmation_code.code != code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неправильный код',
        )

    user = await UserRepo.get_by_id(
        user_id=confirmation_code.user_id, db_session=db_session
    )
    if user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Пользователь не найден',
        )
    user.email_verified = True
    db_session.add(user)
    await db_session.flush()

    await ConfirmationCodeRepo.mark_as_used(
        confirmation_code=confirmation_code, db_session=db_session
    )
    return BaseResponse(message='Почта подтверждена. Можно входить')


@router.post(
    '/restore-password/request/',
    response_model=BaseResponse,
    responses=get_responses(404),
)
async def request_password_restoration_code(
    email: EmailStr,
    db_session: AsyncSession = Depends(get_session),
):
    user = await UserRepo.get_by_email(email=email, db_session=db_session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Неправильный адрес электронной почты',
        )
    confirmation_code = await ConfirmationCodeRepo.create(
        user_id=user.id,
        reason=ConfirmationType.password_reset,
        db_session=db_session,
    )
    link = (
        urljoin(front_config.address, front_config.change_password_endpoint)
        + '?'
        + urlencode({'code': confirmation_code.code})
    )
    message = SendEmailScheme(
        to_address=email,
        from_address=unisender_config.from_address,
        from_name=unisender_config.from_name,
        subject=unisender_config.password_recovery_subject,
        template_id=unisender_config.password_recovery_template_id,
        params={'link': link},
    )
    publish_message(
        rabbitmq_config.mail_topic, message.model_dump(mode='json')
    )
    return BaseResponse(message='Сообщение отправляется на почту')


@router.patch(
    '/restore-password/confirm/',
    response_model=BaseResponse,
    responses=get_responses(400, 404),
)
async def restore_password(
    request_data: ResetPasswordScheme,
    db_session: AsyncSession = Depends(get_session),
):
    confirmation_code = await ConfirmationCodeRepo.get(
        value=request_data.code,
        reason=ConfirmationType.password_reset,
        db_session=db_session,
    )
    if not confirmation_code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Код восстановления пароля не найден',
        )
    new_password_hash = get_password_hash(request_data.new_password)
    await UserRepo.update_password_hash(
        user_id=confirmation_code.user_id,
        new_password_hash=new_password_hash,
        db_session=db_session,
    )
    await ConfirmationCodeRepo.mark_as_used(
        confirmation_code=confirmation_code, db_session=db_session
    )
    return BaseResponse(message='Пароль успешно изменён')


@router.post(
    '/refresh/', response_model=BaseResponse, responses=get_responses(400, 401)
)
async def refresh_tokens(
    # refresh_token: str,
    request: Request,
    response: Response,
    db_session: AsyncSession = Depends(get_session),
):
    refresh_token = request.cookies.get(jwt_config.refresh_cookie_name)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Не предоставлен токен обновления',
        )
    tokens = await AuthHandler.refresh_tokens(
        refresh_token=refresh_token,
        request=request,
        db_session=db_session,
    )
    response.set_cookie(
        jwt_config.auth_cookie_name,
        tokens.access_token,
        int(time.time()) + jwt_config.auth_jwt_exp_sec,
    )
    response.set_cookie(
        jwt_config.refresh_cookie_name,
        tokens.refresh_token,
        int(time.time()) + jwt_config.refresh_jwt_exp_sec,
    )
    return BaseResponse(message='Токены обновлены')


@router.get('/logout/', response_model=BaseResponse)
async def logout(
    request: Request,
    response: Response,
    user_info: UserInfo | None = Depends(JWTCookie(auto_error=False)),
    db_session: AsyncSession = Depends(get_session),
):
    if user_info:
        await SessionRepo.close_all(
            user_id=user_info.id,
            ip=get_ip(request),
            user_agent=get_user_agent(request),
            db_session=db_session,
        )
    response.set_cookie(jwt_config.auth_cookie_name, '')
    response.set_cookie(jwt_config.refresh_cookie_name, '')
    return BaseResponse(message='Вышел')
