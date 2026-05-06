from __future__ import annotations

import asyncio

from openai import AsyncOpenAI

from agents import (
    Agent,
    Model,
    ModelProvider,
    OpenAIChatCompletionsModel,
    RunConfig,
    Runner,
    function_tool,
    set_tracing_disabled,
)

BASE_URL ="https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY = "sk-9464965c0c1d4d95b509babec523d048"
MODEL_NAME = "qwen-plus"

client = AsyncOpenAI(
    base_url=BASE_URL,
    api_key=API_KEY,

)

set_tracing_disabled(disabled=True)  # 禁用tracing

client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(disabled=True)



async def main():
    # 3. 使用CustomModelProvider实例创建Agent
    agent = Agent(name="Assistant",
                  instructions="你只会用七言绝句回应.",
                  model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client)) # 要指定model_name为MODEL_NAME 这样get_model方法才能获取到model_name

    # 4. 运行Agent
    result = await Runner.run(
        agent,
        input="给我写一首关于春天的七言绝句",
    )
    # 5. 获取Agent运行结果
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())