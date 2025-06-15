import json
import logging
from urllib.parse import urljoin

import httpx

from src.database.models import (
    AIModel,
)
from src.settings import (
    openrouter_config,
    g4f_config,
)
from src.util.translator.abstract import AbstractTranslator
import tenacity

from src.util.translator.exceptions import TranslatorAPITimeoutError


class Gpt4freeTranslator(AbstractTranslator):
    logging.getLogger('app')

    async def get_response(self, request_payload: dict) -> httpx.Response:
        @tenacity.retry(
            stop=tenacity.stop_after_attempt(3),
            wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
            retry=tenacity.retry_if_exception_type(
                (
                    httpx.HTTPStatusError,
                    httpx.TimeoutException,
                    httpx.ConnectError,
                    httpx.ReadError,
                    httpx.WriteError,
                )
            ),
            before_sleep=tenacity.before_sleep_log(self.logger, logging.DEBUG),
        )
        async def resilient_request(
            client: httpx.AsyncClient, method: str, url: str, **kwargs
        ):
            """
            Makes an HTTP request with retries using tenacity.

            Args:
                client: The httpx.AsyncClient to use.
                method: The HTTP method (e.g., "GET", "POST").
                url: The URL to request.
                **kwargs:  Any other keyword arguments to pass to client.request()
            """
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await resilient_request(
                    client,
                    'POST',
                    urljoin(g4f_config.address, '/v1/chat/completions'),
                    json=request_payload,
                )
                self.logger.debug('Received repsonse: %s', response)
                return response
            except tenacity.RetryError as e:
                self.logger.error(
                    f'Request failed after multiple retries: {e}'
                )
                raise TranslatorAPITimeoutError()
            except Exception as e:
                self.logger.exception(f'An unexpected error occurred: {e}')
                raise e

    async def _process_chunk(
        self, model: AIModel, prompt: str, chunk: str
    ) -> tuple[str, int]:
        request_payload = {
            'messages': [
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': chunk},
            ],
            'model': model.name,
            'provider': model.provider,
            # 'stream': False,
            # 'temperature': 1,
            # 'max_tokens': 8192,
            # 'stop': [],
            'api_key': openrouter_config.api_key,
            # 'web_search': True,
            # 'proxy': None
        }
        self.logger.info(
            f'Translating chunk: {json.dumps(chunk, ensure_ascii=False)}'
        )
        response = await self.get_response(request_payload)
        payload = response.json()
        self.logger.info('Got response: %s', payload)
        if not response.is_success:
            raise Exception(json.dumps(payload))
        answer = payload['choices'][0]['message']['content']
        tokens_used = payload['usage']['total_tokens']
        self.logger.info(f'Returned answer: {answer}')
        return answer, tokens_used
