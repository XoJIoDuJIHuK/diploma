from typing import Any
import uuid
from datetime import datetime

from pydantic import Field, model_validator

from src.database.models import ReportStatus, Report
from src.responses import Scheme


class FilterReportsScheme(Scheme):
    status: ReportStatus | None = None
    reason_id: int | None = None
    user_id: uuid.UUID | None = None
    article_id: uuid.UUID | None = None


class CreateReportScheme(Scheme):
    text: str = Field(min_length=1, max_length=1024)
    reason_id: int


class EditReportScheme(CreateReportScheme):
    pass


class ReportListItemScheme(Scheme):
    article_id: uuid.UUID
    article_title: str
    status: ReportStatus
    reason_text: str
    text: str
    closed_at: datetime | None = None
    created_at: datetime
    closed_by_user_name: str | None = None
    created_by_user_name: str

    @classmethod
    def create(cls, report_object: Report, **kwargs):
        closed_by_user = report_object.closed_by_user
        closed_by_user_name = closed_by_user.name if closed_by_user else None
        return cls(
            article_id=report_object.article_id,
            article_title=report_object.article.title,
            status=report_object.status,
            closed_at=report_object.closed_at,
            created_at=report_object.created_at,
            closed_by_user_name=closed_by_user_name,
            created_by_user_name=report_object.article.user.name,
            reason_text=report_object.reason.text,
            text=report_object.text,
        )


class ReportOutScheme(ReportListItemScheme):
    text: str = Field(min_length=1, max_length=1024)
    source_text: str
    source_title: str
    source_language_id: int | None
    translated_text: str
    translated_language_id: int
    user_name: str

    @classmethod
    def create(cls, report_object: Report, **kwargs):
        required_kwargs = [
            'source_text',
            'source_title',
            'source_language_id',
            'translated_text',
            'translated_language_id',
            'user_name',
        ]
        if len(set(required_kwargs).difference(set(kwargs))) != 0:
            raise Exception(
                f'ReportOutScheme.create expected {required_kwargs}'
                f', got {kwargs.keys()}'
            )
        articles_info = {}
        for key in required_kwargs:
            articles_info[key] = kwargs.get(key)
        closed_by_user = report_object.closed_by_user
        closed_by_user_name = closed_by_user.name if closed_by_user else None
        return cls(
            text=report_object.text,
            article_id=report_object.article_id,
            article_title=report_object.article.title,
            status=report_object.status,
            closed_at=report_object.closed_at,
            created_at=report_object.created_at,
            closed_by_user_name=closed_by_user_name,
            created_by_user_name=report_object.article.user.name,
            reason_text=report_object.reason.text,
            **articles_info,
        )


class ReportReasonOutScheme(Scheme):
    id: int
    text: str


class CreateCommentScheme(Scheme):
    text: str = Field(min_length=1, max_length=1000)


class CommentOutScheme(CreateCommentScheme):
    text: str
    sender_id: uuid.UUID
    sender_name: str
    created_at: datetime
