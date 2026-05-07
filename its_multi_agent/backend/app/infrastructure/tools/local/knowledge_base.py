import asyncio
from typing import Dict
import httpx
from agents import function_tool
from infrastructure.loggging.logger import logger
from config.settings import settings
@function_tool
async def query_knowledge(question: str) -> Dict:
    """
          查询电脑问题知识库服务,用于检索与用户问题相关的技术文档或解决方案。

          Args:
              question (Optional[str]): 需要查询的具体问题文本。

          Returns:
              dict: 包含查询结果的字典。包含 'question':用户输出问题 ‘answer’:答案
       """

    async with httpx.AsyncClient(trust_env=False) as client:
        try:
            response = await client.post(
                url = f"{settings.KNOWLEDGE_BASE_URL}/query",
                json = {"question": question},
                timeout = 60)
            response.raise_for_status()
            response = await client.post(
                url=f"{settings.KNOWLEDGE_BASE_URL}/query",
                json={"question": question},
                timeout=60
            )

            print(response.status_code)
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"发送请求获取知识库服务下的知识库数据失败:{str(e)}")
            return{"status": "error" , "error_message": f"发送请求获取知识库服务下的知识库数据失败:{e}"}
        except Exception as e:
            logger.error(f"位置错误:{str(e)}")
            return {"status": "error", "error_message": f"未知错误:{e}"}


async def main():
    result = await query_knowledge(question="电脑不能开机怎么解决?")
    print(result)

if __name__ == '__main__':

    asyncio.run(main())