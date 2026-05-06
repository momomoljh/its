import asyncio


from openai import AsyncOpenAI

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
from openai.types.responses import ResponseTextDeltaEvent
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
API_KEY =  "sk-9464965c0c1d4d95b509babec523d048"
MODEL_NAME = "qwen-plus"

# 1. 创建AsyncOpenAI客户端实例
client = AsyncOpenAI(base_url=BASE_URL, api_key=API_KEY)
set_tracing_disabled(disabled=True)


async def main():
    # 2. 创建Agent实例
    agent = Agent(
        name="Assistant",
        instructions="你只会用七言绝句回应.",
        model=OpenAIChatCompletionsModel(model=MODEL_NAME, openai_client=client), # 3.通过Agent的model参数指定使用OpenAIChatCompletionsModel
    )

    # 4. 运行Agent
    result =  Runner.run_streamed(agent, "给我写一首关于春天的七言绝句")
    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(event.data.delta, end="", flush=True)


    print("\n\n===== 流结束 =====")
    print("最终完整结果：", result.final_output)


if __name__ == "__main__":
    asyncio.run(main())