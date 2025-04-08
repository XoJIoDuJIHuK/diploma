from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    AIModel,
    Article,
    Report,
    ReportReason,
    ReportStatus,
    TranslationTask, StylePrompt,
)


class AnalyticsRepo:
    @staticmethod
    async def get_prompts_stats(
            db_session: AsyncSession,
    ) -> dict:
        query = (
            select(StylePrompt.title, Report.status, func.count())
            .select_from(StylePrompt)
            .join(TranslationTask, TranslationTask.prompt_id == StylePrompt.id)
            .join(Article, Article.id == TranslationTask.translated_article_id)
            .join(Report, Report.article_id == Article.id)
            .join(ReportReason, ReportReason.id == Report.reason_id)
            .group_by(StylePrompt.title, Report.status)
            .order_by(StylePrompt.title, Report.status)
        )
        result = await db_session.execute(query)
        # TODO: try rewrite using defaultdicts
        ret = {}
        for prompt_title, report_status, rows_count in result.all():
            if prompt_title not in ret:
                ret[prompt_title] = {}
            ret[prompt_title][report_status] = rows_count
        return ret

    @staticmethod
    async def get_models_stats(
            db_session: AsyncSession,
    ) -> dict:
        query = (
            select(
                AIModel.show_name, Report.status, func.count()
            )
            .select_from(AIModel)
            .join(TranslationTask, TranslationTask.model_id == AIModel.id)
            .join(Article, Article.id == TranslationTask.translated_article_id)
            .join(Report, Report.article_id == Article.id)
            .join(ReportReason, ReportReason.id == Report.reason_id)
            .group_by(AIModel.show_name, Report.status)
            .order_by(AIModel.show_name, Report.status)
        )
        result = await db_session.execute(query)
        ret = {}
        for model_name, report_status, rows_count in result.all():
            if model_name not in ret:
                ret[model_name] = {}
            ret[model_name][report_status] = rows_count
        return ret
