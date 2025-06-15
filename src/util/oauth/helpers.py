from fastapi import HTTPException, status

from src.settings import providers, OAuthProvider
from src.util.oauth import oauth_provider_classes
from src.util.oauth.base import BaseOauth2Authorize
from src.util.oauth.schemes import OAuthCredentialsScheme
from src.util.storage.abstract import AbstractStorage


def get_oauth_provider(
    provider: OAuthProvider,
    storage: AbstractStorage | None = None,
) -> BaseOauth2Authorize:
    """
    Returns suitable oauth provider class by provider name
    """
    config = providers.get(provider.value)
    provider_not_registered_error = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Провайдер не зарегистрирован',
    )

    if config is None:
        raise provider_not_registered_error

    oauth_class = oauth_provider_classes.get(provider.value)

    if not oauth_class:
        raise provider_not_registered_error
    credentials = OAuthCredentialsScheme(
        client_id=config.CLIENT_ID,
        client_secret=config.CLIENT_SECRET,
    )

    return oauth_class(config=config, credentials=credentials, storage=storage)
