import time
import asyncio
import logging
from telethon.sync import TelegramClient

from db_interaction import DataBaseInteraction
from preprocessing import Preprocessing

from shared import settings
from params import RU_CHANNELS, UA_CHANNELS

import logging
logging.getLogger().setLevel(logging.INFO)


class PG_parser:

    def __init__(
        self,
        name: str = settings.PARSER_TG_NAME,
        api_id: int = settings.PARSER_API_ID,
        api_hash: str = settings.PARSER_API_HASH
        ):
        
        self.name = name
        self.api_id = api_id
        self.api_hash = api_hash

        self.preprocessing = Preprocessing()
        self.database = DataBaseInteraction()

    async def parse_ru(self):

        self.last_date = await self.database.get_last_date()

        async with TelegramClient(
            self.name,
            self.api_id,
            self.api_hash,
            device_model = "iPhone 13 Pro Max",
            system_version = "14.8.1",
            app_version = "8.4",
            lang_code = "en",
            system_lang_code = "en-US"
            ) as client:
            
            for index in range(len(RU_CHANNELS)):
                try:
                    async for message in client.iter_messages(RU_CHANNELS[index]):
                        if message.date.timestamp() > self.last_date:

                            text = message.text

                            if text is None or text == '':
                                continue

                            if type(text) != float:
                                
                                tokens = self.preprocessing.preprocess(text)

                                await self.database.insert_post(
                                    message_id=message.id,
                                    sender=RU_CHANNELS[index],
                                    chat_title=message.chat.title,
                                    date=message.date.timestamp(),
                                    text=text,
                                    tokens=tokens
                                )
                        else:
                            break
                except Exception as error:
                    logging.error(error)
                    pass


pg_parser = PG_parser()

async def main():
    while True:
        logging.info('Start parsing')
        await pg_parser.parse_ru()
        time.sleep(600)

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(main())
    