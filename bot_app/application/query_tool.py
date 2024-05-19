from sqlalchemy import desc, func, select, update, text, between
from sqlalchemy.ext.asyncio import async_sessionmaker

from shared.dbs.postgresql import async_session
from shared.models import RuTgData


class QueryTool:
    def __init__(
        self,
        pool: async_sessionmaker = async_session
    ) -> None:
        
        self.pool = pool
        
    async def get_data_by_dates(
        self,
        start_date: int,
        end_date: int
        ):
            
        stmt = select(RuTgData).where(between(RuTgData.date, start_date, end_date))
    
        async with self.pool() as session:
            response = await session.execute(stmt)
            data = response.fetchall()
            
        return data
        
    