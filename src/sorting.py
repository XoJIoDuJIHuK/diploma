from fastapi import HTTPException, status
from pydantic import BaseModel


class SortingParams(BaseModel):
    sort_by: str | None = None
    desc: bool = True


def get_sorted_query(query, model, sorting_params: SortingParams):
    if sorting_params.sort_by is None:
        return query
    field = getattr(model, sorting_params.sort_by)
    if field is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f'Атрибут {sorting_params.sort_by} отсутствует в данной модели',
        )
    return query.order_by(field.desc() if sorting_params.desc else field.asc())
