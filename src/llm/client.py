import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from .prompts import SYSTEM_PROMPT, user_prompt

load_dotenv(override=True)

_NOT_RELEVANT_SENTINEL = "NO_RELEVANT_CONTENT"
NOT_RELEVANT_MESSAGE = (
    "The fetched page does not contain content relevant to the query."
)

LLM_BASE_URL = os.getenv('LLM_BASE_URL')
LLM_MODEL    = os.getenv('LLM_MODEL')

class ContentExtractor:
    def __init__(self) -> None:
        base_url = LLM_BASE_URL
        model = LLM_MODEL

        self._model = model
        self._client = AsyncOpenAI(
            base_url=base_url, 
            api_key="dummy"
        )

    async def extract_relevant(self, content: str, query: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt(content, query)},
            ],
        )
        answer = (response.choices[0].message.content or "").strip()

        if answer == _NOT_RELEVANT_SENTINEL:
            return NOT_RELEVANT_MESSAGE

        return answer
