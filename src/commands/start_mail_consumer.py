import asyncio

import logging
from src.settings import rabbitmq_config

import click

from src.util.brokers.consumer.rabbitmq import MailConsumer

logger = logging.getLogger('app')


@click.command('start_mail_consumer')
def start_mail_consumer():
    logger.info("Starting mail consumer")
    try:
        asyncio.run(MailConsumer().run(rabbitmq_config.mail_topic))
    except Exception as e:
        logger.exception(e)
