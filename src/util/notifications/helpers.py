from sqlalchemy.ext.asyncio import AsyncSession

from src.database.repos.notification import NotificationRepo
import logging
from src.routers.notifications.schemes import (
    NotificationCreateScheme,
    NotificationOutScheme,
)
from src.settings import notification_config
from src.util.storage.classes import RedisHandler


logger = logging.getLogger('app')


async def send_notification(
    notification_scheme: NotificationCreateScheme,
    db_session: AsyncSession,
) -> None:
    logger.warning(
        f'Sending notification {notification_scheme.title} '
        f'to {notification_scheme.user_id}'
    )
    notification = await NotificationRepo.create(
        notification_scheme, db_session
    )
    redis_client = RedisHandler().client
    await redis_client.publish(
        notification_config.topic_name.format(notification_scheme.user_id),
        message=(
            NotificationOutScheme.model_validate(
                notification
            ).model_dump_json()
        ),
    )
