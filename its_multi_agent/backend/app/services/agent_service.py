import re
import traceback
from collections.abc import AsyncGenerator

from infrastructure.logging.logger import logger
from multi_agent.orchestrator_agent import orchestrator_agent
from schemas.request import ChatMessageRequest
from agents.run import RunConfig,Runner

from schemas.response import ContentKind
from services.session_service import session_service
from services.stream_response_service import process_stream_response
from utils.response_util import ResponseFactory


class MultiAgentService:


   @classmethod
   async def process_task(cls, request: ChatMessageRequest,flag:bool)->AsyncGenerator:
      """
      多智能体任务入口
      Args:
         request: 请求上下文

      Returns:
         AsyncGenerator: 异步生成器对象 必须
      """
      try:
         # 1.获取请求上下文
         user_id = request.context.user_id
         session_id = request.context.session_id
         user_query = request.query
         # 2. 准备历史对话
         chat_history = session_service.prepare_history(user_id, session_id, user_query)
         # 3. 运行agent
         streaming_result = Runner.run_streamed(
            starting_agent = orchestrator_agent,
            input = chat_history,
            context = user_query,
            max_turns = 3, #  COT行动链迭代多少次 不是异常重试
            run_config = RunConfig(tracing_disabled = True),
         )

         # 4. 处理agent事件
         async for event in process_stream_response(streaming_result):
            yield event
         # 5. 获取agent结果
         agent_result = streaming_result.final_output
         clean_result = re.sub(r'\n+', '\n', agent_result)
         # 6. 存储历史对话
         chat_history.append({"role": "assistant","content":clean_result})
         session_service.save_history(user_id, session_id, chat_history)
      except Exception as e:
         # 记录错误日志
         logger.error(f"AgentService.process_query执行出错: {str(e)}")
         logger.debug(f"异常详情: {traceback.format_exc()}")

         text = f"❌ 系统错误: {str(e)}"
         yield "data: " + ResponseFactory.build_text(
            text, ContentKind.PROCESS
         ).model_dump_json() + "\n\n"

         # 7. 异常重试
         # 如果允许重试，则启动重试流程
         if flag:
            text = f"🔄 正在尝试自动重试..."
            yield "data: " + ResponseFactory.build_text(
               text, ContentKind.PROCESS
            ).model_dump_json() + "\n\n"

            # 递归调用进行重试
            async for item in MultiAgentService.process_task(request, flag=False):
               yield item
