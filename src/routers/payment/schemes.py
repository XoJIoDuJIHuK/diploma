import datetime
import uuid
from src.database.models import BalanceChangeCause
from src.responses import Scheme


class ProductScheme(Scheme):
    id: str
    default_price: str
    name: str


class PriceOutScheme(Scheme):
    amount: int
    currency: str


class ProductOutScheme(Scheme):
    id: str
    name: str
    price: PriceOutScheme


class SessionScheme(Scheme):
    user_id: uuid.UUID
    tokens_amount: int


class TransactionOutScheme(Scheme):
    tokens_amount: int
    cause: BalanceChangeCause
    created_at: datetime.datetime
