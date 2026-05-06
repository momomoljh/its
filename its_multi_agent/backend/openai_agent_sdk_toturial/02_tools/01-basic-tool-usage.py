from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()
import json
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)
def get_age(name: str) -> str:
    age = {
        "小明": "2",
        "小红": "1",
        "小花": "3",
    }
    return age.get(name,f"暂无{name}的信息")
messages = [
        {"role" : "system", "content":"你是一个年龄助手，可以查询年龄信息。"},
        {"role" : "user", "content": "我想知道小红几岁"},
    ]
responses = client.chat.completions.create(
    model = os.getenv("OPENAI_MODEL_NAME"),
    messages = messages,
    tools = [{
        "type": "function",
        "function": {
            "name": "get_age",
            "description": "查询指定用户的年龄",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "用户，如'小明'、'小红'",
                    },
                },
                "required": ["name"],
                "additionalProperties": False
            },
        },
    }]
)
print(responses)

message = responses.choices[0].message
messages.append(message)

if message.tool_calls:
    for tool_call in message.tool_calls:
        if tool_call.function.name == "get_age":
            args = json.loads(tool_call.function.arguments)
            result = get_age(args["name"])  # 调用工具
            print(result)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })
            messages = messages

        second_response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL_NAME"),
            messages=messages,
    )
    print(f"最终回复: {second_response.choices[0].message.content}")
