import uuid

from pydantic import Field

from src.responses import Scheme
from src.settings import simple_translation_config


class EstimationRequestScheme(Scheme):
    text: str


class EstimationResponseScheme(Scheme):
    tokens: int


class TranslationBase(Scheme):
    target_language_id: int
    model_id: int
    prompt_id: int


class SimpleTranslationRequestScheme(TranslationBase):
    text: str = Field(max_length=simple_translation_config.text_max_length)
    source_language_id: int | None


class SimpleTranslationOutScheme(Scheme):
    text: str


class CreateTaskScheme(TranslationBase):
    article_id: uuid.UUID


class CreateTranslationScheme(Scheme):
    article_id: uuid.UUID
    target_language_ids: list[int]
    prompt_id: int
    model_id: int
