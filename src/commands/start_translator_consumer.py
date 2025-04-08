import asyncio

import click

from src.logger import get_logger
from src.settings import rabbitmq_config
from src.util.brokers.consumer.rabbitmq import TranslationConsumer

logger = get_logger(__name__)


@click.command('start_translator_consumer')
def start_translator_consumer():
    try:
        asyncio.run(
            TranslationConsumer().run(rabbitmq_config.translation_topic)
        )
    except Exception as e:
        logger.exception(e)
