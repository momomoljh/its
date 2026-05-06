from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("AL_BAILIAN_API_KEY"),
    base_url=os.getenv("AL_BAILIAN_BASE_URL")
)
responses = client.responses.create(
    model = os.getenv("AL_BAILIAN_MODEL_NAME"),
    input="你是谁"
)
print(responses.output_text)

