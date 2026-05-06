from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
responses = client.responses.create(
    model = os.getenv("OPENAI_MODEL_NAME"),
    input="你是谁"
)
print(responses.output_text)
