from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
responses = client.chat.completions.create(
    model = os.getenv("OPENAI_MODEL_NAME"),
    messages = [
        {"role" : "system", "content":"你是一个专业python开发人员"},
        {"role" : "user", "content": "你是谁"}
    ]
)
print(responses.choices[0].message.content)
