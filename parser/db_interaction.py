import datetime
from sqlalchemy import select, update, insert, func
from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.dbs.postgresql import async_session
from shared.models import RuTgData

import logging
logging.getLogger().setLevel(logging.INFO)

class DataBaseInteraction:
    def __init__(
        self,
        pool: async_sessionmaker = async_session
        ):
        
        self.pool = pool
    
    async def insert_post(
        self,
        message_id: int,
        sender: str,
        chat_title: str,
        date: int,
        text: str,
        tokens: list[str]
        ):
        
        stmt = insert(RuTgData) \
                .values(
                    message_id=message_id,
                    sender=sender,
                    chat_title=chat_title,
                    date=date,
                    text=text,
                    tokens=tokens
                    )
                
        async with self.pool() as session:
            await session.execute(stmt)
            await session.commit()
            
    async def get_last_date(self):
        
        stmt = select(func.max(RuTgData.date))
        
        async with self.pool() as session:
            last_date = await session.execute(stmt)
            last_date = last_date.fetchone()[0]
            
        logging.info(f'last_date: {last_date}')

        if last_date is None:
            return (datetime.datetime.now() - datetime.timedelta(days=3)).timestamp()
        else:
            return last_date
                