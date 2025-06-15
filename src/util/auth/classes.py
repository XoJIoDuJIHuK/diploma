import time
import uuid

from fastapi import HTTPException, Request, status
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    APIKeyCookie,
)

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Session, User
from src.database.repos.session import SessionRepo
import logging
from src.settings import jwt_config, LOGGER_PREFIX, Role
from src.util.auth.helpers import (
    get_user_agent,
    verify_jwt,
    put_tokens_in_black_list,
)
from src.util.auth.schemes import TokensScheme, RefreshPayload
from src.util.common.helpers import get_ip
from src.util.storage.classes import RedisHandler


logger = logging.getLogger('app')


class JWTBearer(HTTPBearer):
    def __init__(
        self, roles: list[Role] | None = None, auto_error: bool = True
    ):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.roles = roles if roles else []
        self.logger = logging.getLogger('app')

    async def __call__(self, request: Request):
        credentials: HTTPAuthorizationCredentials
        try:
            credentials = await super(JWTBearer, self).__call__(request)
        except HTTPException as e:
            self.logger.info('User provided invalid credentials: %s', e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Неправильные данные входа',
            )

        error_invalid_token = HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Неправильный токен',
        )
        error_no_rights = HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail='Недостаточно прав'
        )

        if credentials:
            if not credentials.scheme == 'Bearer':
                raise error_invalid_token
            if not (payload := verify_jwt(credentials.credentials)):
                raise error_invalid_token
            provided_role = payload.role
            if not await self.role_allowed(provided_role):
                raise error_no_rights

            return payload
        else:
            return None

    async def role_allowed(self, provided_role: Role) -> bool:
        if len(self.roles) == 0:
            return True
        if not provided_role:
            return False
        return provided_role in self.roles


class JWTCookie(APIKeyCookie):
    def __init__(
        self,
        roles: list[Role] | None = None,
        auto_error: bool = True,
        cookie_name: str = jwt_config.auth_cookie_name,
    ):
        super(JWTCookie, self).__init__(
            auto_error=auto_error,
            name=cookie_name,
        )
        self.roles = roles if roles else []
        self.logger = logging.getLogger('app')

    async def __call__(self, request: Request):
        token: str
        error_invalid_token = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Неправильные данные входа',
        )

        try:
            token = await super(JWTCookie, self).__call__(request)
        except HTTPException as e:
            self.logger.warning('User provided invalid credentials: %s', e)
            raise error_invalid_token

        if not token:
            return None
        payload = verify_jwt(token)
        if not payload:
            if self.auto_error:
                self.logger.warning('Token payload invalid: %s', token)
                raise error_invalid_token
            else:
                return None
        if not self.role_allowed(self.roles, payload.role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Недостаточно прав',
            )
        if payload.user_agent != get_user_agent(request):
            self.logger.warning(
                'User agent mismatch: %s | %s',
                payload.user_agent,
                get_user_agent(request),
            )
            if self.auto_error:
                return None
            raise error_invalid_token

        return payload

    @staticmethod
    def role_allowed(roles: list[Role], provided_role: Role) -> bool:
        if len(roles) == 0:
            return True
        if not provided_role:
            return False
        return provided_role in roles


class AuthHandler:
    @classmethod
    async def login(
        cls, user: User, request: Request, db_session: AsyncSession
    ) -> TokensScheme:
        refresh_token_id = uuid.uuid4()
        logger.info(request.headers)
        session = Session(
            user_id=user.id,
            refresh_token_id=refresh_token_id,
            ip=get_ip(request),
            user_agent=get_user_agent(request),
        )
        db_session.add(session)
        await db_session.flush()

        await db_session.refresh(session)
        await db_session.refresh(user)
        return cls.get_tokens_scheme(
            user_id=user.id,
            user_agent=session.user_agent,
            session_id=session.id,
            role=user.role,
            refresh_token_id=refresh_token_id,
        )

    @classmethod
    async def refresh_tokens(
        cls, refresh_token: str, request: Request, db_session: AsyncSession
    ) -> TokensScheme:
        payload: RefreshPayload = verify_jwt(
            token=refresh_token, is_access=False
        )
        if not payload or await RedisHandler().get(str(payload.token_id)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Сессия истекла',
            )
        await put_tokens_in_black_list([payload.token_id])

        # This operation is much heavier than getting info from Redis
        # but will happen only if session was not expired so refresh tokens of
        # expired sessions will not trigger querying database
        session = await SessionRepo.get_by_refresh_id(
            refresh_token_id=payload.token_id, db_session=db_session
        )
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Сессия пользователя не обнаружена',
            )
        session_id = session.id
        session_ip = session.ip
        user_agent = session.user_agent

        if (
            get_user_agent(request) != user_agent
            or get_ip(request) != session_ip
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='Обнаружена смена устройства. Войдите заново',
            )

        new_refresh_token_id = uuid.uuid4()
        session.refresh_token_id = new_refresh_token_id
        db_session.add(session)
        await db_session.flush()

        await db_session.refresh(session)
        return cls.get_tokens_scheme(
            user_id=payload.id,
            user_agent=get_user_agent(request),
            session_id=session_id,
            refresh_token_id=new_refresh_token_id,
            role=payload.role,
        )

    @classmethod
    def get_access_token(
        cls, user_id: uuid.UUID, user_agent: str, role: Role
    ) -> str:
        access_payload = {
            jwt_config.user_info_property: {
                'id': str(user_id),
                'user_agent': user_agent,
                'role': role.value,
            },
            'exp': int(time.time()) + jwt_config.auth_jwt_exp_sec,
        }
        return jwt.encode(
            access_payload, jwt_config.secret_key, jwt_config.algorithm
        )

    @classmethod
    def get_refresh_token(
        cls,
        user_id: uuid.UUID,
        user_agent: str,
        session_id: uuid.UUID,
        refresh_token_id: uuid.UUID,
        role: Role,
    ) -> str:
        refresh_payload = {
            jwt_config.user_info_property: {
                'id': str(user_id),
                'role': role.value,
                'user_agent': user_agent,
                'session_id': str(session_id),
                'token_id': str(refresh_token_id),
            },
            'exp': int(time.time()) + jwt_config.refresh_jwt_exp_sec,
        }
        return jwt.encode(
            refresh_payload, jwt_config.secret_key, jwt_config.algorithm
        )

    @classmethod
    def get_tokens_scheme(
        cls,
        user_id: uuid.UUID,
        user_agent: str,
        session_id: uuid.UUID,
        role: Role,
        refresh_token_id: uuid.UUID,
    ) -> TokensScheme:
        access_token = cls.get_access_token(user_id, user_agent, role)
        refresh_token = cls.get_refresh_token(
            user_id, user_agent, session_id, refresh_token_id, role
        )
        return TokensScheme(
            access_token=access_token, refresh_token=refresh_token
        )
