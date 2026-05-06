import asyncio


from openai import AsyncOpenAI

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled

BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY =  "sk-9464965c0c1d4d95b509babec523d048"
MODEL_NAME = "qwen-plus"

# 1. 创建AsyncOpenAI客户端实例
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(disabled=True)

@function_tool
def get_weather(city: str) -> str:
    """获取指定城市的天气信息"""
    return f"天气信息: {city} 是晴天"


async def main():
    # 2. 创建Agent实例
    agent = Agent(
        name="天气助手",
        instructions="你是一个天气助手，你只能回答关于天气的问题。",
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client), # 3.通过Agent的model参数指定使用OpenAIChatCompletionsModel
        tools = [get_weather]
    )

    # 4. 运行Agent
    result = await Runner.run(agent, "杭州的天气")

    # 5. 获取Agent运行结果
    print(result.final_output)


if __name__ == "__main__":
    asyncio.run(main())