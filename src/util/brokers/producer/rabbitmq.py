import json
from pika import BlockingConnection, ConnectionParameters, credentials
from src.logger import get_logger
from src.settings import rabbitmq_config

logger = get_logger(__name__)


def publish_message(routing_key: str, message: dict):
    connection = BlockingConnection(
        ConnectionParameters(
            rabbitmq_config.host,
            credentials=credentials.PlainCredentials(
                rabbitmq_config.login,
                rabbitmq_config.password,
            ),
        )
    )
    channel = connection.channel()
    channel.queue_declare(routing_key)
    channel.basic_publish('', routing_key, json.dumps(message))
    logger.info('Message %s was sent to queue %s', message, routing_key)
    connection.close()
