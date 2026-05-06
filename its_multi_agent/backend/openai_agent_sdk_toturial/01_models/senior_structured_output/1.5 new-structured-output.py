from openai import OpenAI
import os
from pydantic import BaseModel
from dotenv import load_dotenv
load_dotenv()
class Person(BaseModel):
    name: str
    age: int
client = OpenAI(
    api_key=os.getenv("AL_BAILIAN_API_KEY"),
    base_url=os.getenv("AL_BAILIAN_BASE_URL")
)
responses = client.responses.parse(
    model = os.getenv("AL_BAILIAN_MODEL_NAME"),
    instructions="你是4岁的专业Python工程师,You must return name, age fields. Do not return extra text.",
    input = "你是谁",
    text_format=Person
)
print(responses.output_parsed)

