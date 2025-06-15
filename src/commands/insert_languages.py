import asyncio
import json
import sys

import click

from src.database import get_session
from src.database.models import Language

import logging
from src.settings import LOGGER_PREFIX

from sqlalchemy.future import select

logger = logging.getLogger('app')


@click.command()
def insert_languages() -> None:
    with open('contrib/persistent_data/languages.json', 'r') as file:
        languages = json.load(file)

    async def async_function() -> None:
        async with get_session() as db_session:
            db_query = await db_session.execute(select(Language))
            db_languages = db_query.scalars().all()

            language_objects = [
                Language(name=lang, iso_code=iso_code)
                for lang, iso_code in languages.items()
                if iso_code not in map(lambda x: x.iso_code, db_languages)
            ]
            if not language_objects:
                logger.info('No languages to insert')
            else:
                logger.info(
                    f'Inserting languages {
                        [lang.iso_code for lang in language_objects]
                    }'
                )
                db_session.add_all(language_objects)
        logger.info('Languages inserted')

    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_function())
    loop.close()
    sys.exit()
