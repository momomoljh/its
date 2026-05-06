from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
import json
client = OpenAI(
    api_key=os.getenv("AL_BAILIAN_API_KEY"),
    base_url=os.getenv("AL_BAILIAN_BASE_URL")
)
def get_age(name: str) -> str:
    age = {
        "小明": "2",
        "小红": "1",
        "小花": "3",
    }
    return age.get(name,f"暂无{name}的信息")
tools = [
    {
        "type": "function",
        "name": "get_age",
        "description": "获得用户的年龄",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "user e.g. 小红, 小花",
                }
            },
            "required": ["name"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]
responses = client.responses.create(
    model = os.getenv("AL_BAILIAN_MODEL_NAME"),
    input="小明今年几岁",
    tools=tools,
)
print(responses.output)




