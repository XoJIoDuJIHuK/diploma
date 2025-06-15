import asyncio

import click

import logging
from src.settings import rabbitmq_config
from src.util.brokers.consumer.rabbitmq import TranslationConsumer

logger = logging.getLogger('app')


@click.command('start_translator_consumer')
def start_translator_consumer():
    logger.info('Starting translator consumer')
    try:
        asyncio.run(
            TranslationConsumer().run(rabbitmq_config.translation_topic)
        )
    except Exception as e:
        logger.exception(e)
