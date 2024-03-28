import os
import dotenv
from openai import OpenAI

dotenv.load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY", '')


def _chat_with_gpt(prompt: str) -> str:
    raise NotImplementedError
