from datetime import timedelta
import json
import uuid

from fastapi import APIRouter, Request, status, Depends, HTTPException
from fastapi.responses import RedirectResponse

import stripe

from src.database.repos.token_transaction_log import TransactionRepo
from src.responses import ListResponse
from src.pagination import PaginationParams, get_pagination_params
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import BalanceChangeCause
from src.settings import front_config, stripe_config
from src.database.repos.user import UserRepo
from src.depends import get_session
import logging
from src.util.auth.classes import JWTCookie
from src.util.auth.schemes import UserInfo
from src.responses import SimpleListResponse
from src.routers.payment.schemes import (
    ProductOutScheme,
    ProductScheme,
    PriceOutScheme,
    SessionScheme,
    TransactionOutScheme,
)
from src.util.storage.classes import RedisHandler

router = APIRouter(prefix='/payment', tags=['Stripe'])
stripe.api_key = stripe_config.secret_key
logger = logging.getLogger('app')


@router.get('/products/')
async def get_products(
):
    def format_product(
        product_object: stripe.Product,
    ) -> ProductOutScheme:
        product_dict = json.loads(str(product_object))
        price = prices[product_dict['default_price']]
        return ProductOutScheme(
            id=product_dict['id'], name=product_dict['name'], price=price
        )

    prices = {
        price['id']: PriceOutScheme(
            amount=price['unit_amount'],
            currency=price['currency'],
        )
        for price in map(
            lambda x: json.loads(str(x)), await stripe.Price.list_async()
        )
    }

    products = list(
        map(
            format_product,
            list(await stripe.Product.list_async()),
        )
    )

    return SimpleListResponse[ProductOutScheme].from_list(products)


@router.get('/create-checkout-session/{product_id}')
async def create_checkout_session(
    product_id: str,
    user_info: UserInfo = Depends(JWTCookie()),
):
    try:
        product = ProductScheme.model_validate_json(
            str(stripe.Product.retrieve(product_id))
        )
        tokens_amount = int(product.name.split(' ')[0])
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            detail='Товар не найден', status_code=status.HTTP_404_NOT_FOUND
        )

    try:
        redis_client = RedisHandler().client
        session_id = str(uuid.uuid4())

        session_data = SessionScheme(
            user_id=user_info.id,
            tokens_amount=tokens_amount,
        )

        await redis_client.setex(
            name=f'checkout_session:{session_id}',
            time=timedelta(seconds=stripe_config.session_ttl_sec),
            value=session_data.model_dump_json(),
        )
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[
                {
                    'price': product.default_price,
                    'quantity': 1,
                }
            ],
            mode='payment',
            success_url=f'{front_config.address}?session_id={session_id}',
            cancel_url=front_config.address,
            client_reference_id=session_id,
            metadata={'session_id': session_id, 'product_id': product_id},
        )

        logger.info('Session data: %s', session_data)

        if checkout_session.url is None:
            raise Exception(
                f'Checkout session url is None: {checkout_session}'
            )
        return RedirectResponse(checkout_session.url)
    except stripe.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def validate_request(
    request: Request,
):
    try:
        payload = await request.body()
        sig_header = request.headers.get('Stripe-Signature')
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_config.webhook_secret
        )
    except Exception as e:
        logger.error(e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Invalid request payload/headers',
        )


@router.post('/confirm/')
async def confirm_payment(
    request: Request,
    db_session: AsyncSession = Depends(get_session),
    request_is_valid=Depends(validate_request),
):
    redis_client = RedisHandler().client
    payload = await request.json()
    logger.info('Received webhook: %s', payload)
    logger.info('Headers: %s', request.headers)
    session_status = payload['data']['object']['status']
    if session_status != 'complete':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Session must be complete',
        )
    session_id = payload['data']['object']['metadata']['session_id']

    # Get session data from Redis
    session_data = SessionScheme.model_validate_json(
        await redis_client.get(f'checkout_session:{session_id}')
    )
    if not session_data:
        logger.error(
            'Session expired or not found',
        )
        return {'status': 'session expired or not found'}

    await redis_client.delete(f'checkout_session:{session_id}')
    user = await UserRepo.get_by_id(
        user_id=session_data.user_id,
        db_session=db_session,
    )
    await UserRepo.update_balance(
        user_id=session_data.user_id,
        delta=session_data.tokens_amount,
        reason=BalanceChangeCause.purchase,
        db_session=db_session,
    )
    logger.info(
        'User %s received %d tokens', user.name, session_data.tokens_amount
    )

    return {'status': 'success'}


@router.get('/log')
async def get_transactions_log(
    pagination: PaginationParams = Depends(get_pagination_params),
    user_info: UserInfo = Depends(JWTCookie()),
    db_session: AsyncSession = Depends(get_session),
):
    transactions, count = await TransactionRepo.get_by_user(
        user_id=user_info.id,
        pagination_params=pagination,
        db_session=db_session,
    )
    return ListResponse[TransactionOutScheme].from_list(
        items=list(map(TransactionOutScheme.model_validate, transactions)),
        total_count=count,
        params=pagination,
    )
