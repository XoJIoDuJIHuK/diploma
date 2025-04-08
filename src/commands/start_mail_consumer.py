import asyncio

from src.logger import get_logger
from src.settings import rabbitmq_config

import click

from src.util.brokers.consumer.rabbitmq import MailConsumer

logger = get_logger(__name__)


@click.command('start_mail_consumer')
def start_mail_consumer():
    try:
        asyncio.run(MailConsumer().run(rabbitmq_config.mail_topic))
    except Exception as e:
        logger.exception(e)
