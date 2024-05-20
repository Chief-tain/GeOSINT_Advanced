from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from shared import settings


class GPT():
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.GPT_API_KEY)
        self.model: str = settings.GPT_MODEL
        self.temperature: str = 0.3
        
    async def process_chat_completions(
        self,
        promt_styling: str
        ) -> ChatCompletion:

        return await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {
                    "role": "system",
                    "content": promt_styling
                }
            ]
        )
