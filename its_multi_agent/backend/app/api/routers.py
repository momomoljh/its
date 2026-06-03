
from services.agent_service import MultiAgentService
from schemas.request import ChatMessageRequest
from fastapi.routing import APIRouter
from starlette.responses import StreamingResponse

router = APIRouter()

@router.post("/api/query", summary="智能体对话接口")
async def query(request_context: ChatMessageRequest)-> StreamingResponse:
    """
    SSE返回数据(流式响应)
    Args:
        request_context:请求上下文

    Returns:
        streaming_response:
    """
    user_id = request_context.context.user_id
    session_id = request_context.context.session_id
    user_query = request_context.query

    async_generator_result = MultiAgentService.process_task(request_context,True)

    return StreamingResponse(
        content=async_generator_result,
        status_code = 200,
        media_type="text/event-stream"
    )