import asyncio
import json
from abc import ABC
from dataclasses import dataclass
import logging
from src.util.brokers.consumer.exceptions import IntegrityException
from src.util.mail.classes import UnisenderMailSender
from src.util.mail.schemes import SendEmailScheme
from sqlalchemy.ext.asyncio import AsyncSession

from src.util.brokers.consumer.schemes import TranslationMessage
from src.database import get_session
from src.database.models import (
    AIModel,
    Article,
    BalanceChangeCause,
    Language,
    NotificationType,
    StylePrompt,
    TranslationTask,
    TranslationTaskStatus,
)
from src.database.repos.article import ArticleRepo
from src.database.repos.language import LanguageRepo
from src.database.repos.model import ModelRepo
from src.database.repos.prompt import PromptRepo
from src.database.repos.translation_task import TaskRepo
from src.database.repos.user import UserRepo
from src.routers.articles.schemes import CreateArticleScheme
from src.routers.notifications.schemes import NotificationCreateScheme
from src.settings import notification_config, rabbitmq_config
from src.util.notifications.helpers import send_notification
from src.util.translator.classes import Gpt4freeTranslator
from src.util.translator.exceptions import TranslatorAPITimeoutError

from aio_pika import connect, logger as pika_logger
from aio_pika.abc import AbstractIncomingMessage

logger = logging.getLogger('app')
pika_logger.setLevel(logging.WARNING)


@dataclass
class TranslationData:
    task: TranslationTask
    source_article: Article
    source_language: Language | None
    target_language: Language
    prompt: StylePrompt
    model: AIModel


class AbstractAsyncConsumer(ABC):
    async def run(self, queue_name: str):
        logger.info('Starting consumer for queue <%s>', queue_name)
        connection = await connect(
            f'amqp://{rabbitmq_config.login}:{rabbitmq_config.password}@{rabbitmq_config.host}/'
        )

        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            queue = await channel.declare_queue(queue_name)
            await queue.consume(self._on_message)

            await asyncio.Future()
        logger.info('Lmao consumer ended working')

    async def _on_message(self, message: AbstractIncomingMessage):
        pass


class MailConsumer(AbstractAsyncConsumer):
    async def _on_message(self, message: AbstractIncomingMessage):
        async with message.process():
            body = message.body.decode()
            message_scheme = SendEmailScheme.model_validate_json(body)
            logger.info(
                f'Sending {message_scheme.subject} email to {message_scheme.to_address}'
            )
            try:
                await UnisenderMailSender.send(
                    to_address=message_scheme.to_address,
                    from_address=message_scheme.from_address,
                    from_name=message_scheme.from_name,
                    subject=message_scheme.subject,
                    template_id=message_scheme.template_id,
                    params=message_scheme.params,
                )
                logger.warning(
                    f'Message to {message_scheme.to_address} is sent'
                )
                logger.info('Message sent successfully')
            except Exception as e:
                logger.exception(e)


class TranslationConsumer(AbstractAsyncConsumer):
    translator = Gpt4freeTranslator()

    @staticmethod
    async def __check_message_consistency(
        message: TranslationMessage, db_session: AsyncSession
    ) -> TranslationData:
        task = await TaskRepo.get_by_id(
            task_id=message.task_id, db_session=db_session
        )
        if not task:
            raise IntegrityException(
                f'Задача с идентификатором {message.task_id} не найдена'
            )
        article = await ArticleRepo.get_by_id(
            article_id=task.article_id, db_session=db_session
        )
        if not article:
            raise IntegrityException(
                f'Исходная статья не найдена по'
                f' идентификатору: {task.article_id}'
            )
        source_lang = await LanguageRepo.get_by_id(
            language_id=article.language_id, db_session=db_session
        )
        target_lang = await LanguageRepo.get_by_id(
            language_id=task.target_language_id, db_session=db_session
        )
        if not target_lang:
            raise IntegrityException(
                f'Конечный язык не найден по идентификатору:'
                f' {task.target_language_id}'
            )
        model = await ModelRepo.get_by_id(
            model_id=task.model_id,
            db_session=db_session,
        )
        prompt_object = await PromptRepo.get_by_id(
            prompt_id=task.prompt_id,
            db_session=db_session,
        )

        task.status = TranslationTaskStatus.started
        await db_session.flush()

        return TranslationData(
            task=task,
            source_article=article,
            source_language=source_lang,
            target_language=target_lang,
            prompt=prompt_object,
            model=model,
        )

    async def _on_message(self, message: AbstractIncomingMessage):
        task_data = None
        error_message = None
        async with message.process():
            async with get_session() as db_session:
                try:
                    body = message.body.decode()
                    logger.info(
                        f'Received message {body} of type {type(body)}'
                    )
                    message_scheme = TranslationMessage.model_validate(
                        json.loads(body)
                    )

                    task_data = await self.__check_message_consistency(
                        message_scheme, db_session
                    )
                    (
                        translated_title,
                        title_tokens,
                    ) = await self.translator.translate(
                        text=task_data.source_article.title,
                        target_language=task_data.target_language,
                        source_language=task_data.source_language,
                        model=task_data.model,
                        prompt_object=task_data.prompt,
                    )
                    logger.info(f'Translated title: {translated_title}')

                    (
                        translated_text,
                        text_tokens,
                    ) = await self.translator.translate(
                        text=task_data.source_article.text,
                        target_language=task_data.target_language,
                        source_language=task_data.source_language,
                        model=task_data.model,
                        prompt_object=task_data.prompt,
                    )
                    logger.info(f'Translated text: {translated_text}')

                    translated_article = await ArticleRepo.create(
                        article_data=CreateArticleScheme(
                            title=translated_title,
                            text=translated_text,
                            user_id=task_data.source_article.user_id,
                            language_id=task_data.target_language.id,
                            original_article_id=task_data.source_article.id,
                        ),
                        db_session=db_session,
                    )
                    db_session.add(translated_article)
                    await db_session.flush()
                    await db_session.refresh(translated_article)
                    await db_session.refresh(task_data.source_article)

                    task_data.task.status = TranslationTaskStatus.completed
                    task_data.task.translated_article_id = (
                        translated_article.id
                    )
                    await UserRepo.update_balance(
                        user_id=task_data.source_article.user_id,
                        delta=(title_tokens + text_tokens) * -1,
                        reason=BalanceChangeCause.translation,
                        db_session=db_session,
                    )
                    task_data.task.cost = title_tokens + text_tokens
                    await db_session.flush()

                    await db_session.refresh(task_data.task)
                    await db_session.refresh(task_data.target_language)
                    await db_session.refresh(task_data.source_article)
                    await send_notification(
                        notification_scheme=NotificationCreateScheme(
                            title=notification_config.Subjects.translation_ended,
                            text=notification_config.translation_success_message.format(
                                article_name=task_data.source_article.title,
                                target_lang=task_data.target_language.name,
                            ),
                            user_id=task_data.source_article.user_id,
                            type=NotificationType.info,
                        ),
                        db_session=db_session,
                    )
                except IntegrityException as e:
                    error_message = str(e)
                    logger.error(e)
                except TranslatorAPITimeoutError:
                    error_message = (
                        'Сервис перевода не отвечает. Попробуйте позже'
                    )
                except Exception as e:
                    logger.exception(e)
                    error_message = 'Ошибка сервера'

                logger.info('Error message is: %s', error_message)
                if error_message is None:
                    return
                logger.info('task data is %s', task_data)
                if task_data is None:
                    logger.error("Can't send notification: user unknown")
                    return
                await send_notification(
                    notification_scheme=NotificationCreateScheme(
                        title=(notification_config.Subjects.translation_error),
                        text=error_message,
                        type=NotificationType.error,
                        user_id=task_data.source_article.user_id,
                    ),
                    db_session=db_session,
                )
                logger.info('Gracefully returning')
