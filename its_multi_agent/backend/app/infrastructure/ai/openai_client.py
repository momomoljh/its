from config.settings import settings
from agents import OpenAIChatCompletionsModel
from openai import AsyncOpenAI


OPENAI_API_KEY= settings.OPENAI_API_KEY
OPENAI_BASE_URL= settings.OPENAI_BASE_URL

SF_API_KEY= settings.SF_API_KEY
SF_BASE_URL= settings.SF_BASE_URL
MAIN_MODEL_NAME= settings.MAIN_MODEL_NAME


ALI_BAILIAN_API_KEY= settings.ALI_BAILIAN_API_KEY
ALI_BAILIAN_BASE_URL= settings.ALI_BAILIAN_BASE_URL
SUB_MODEL_NAME= settings.SUB_MODEL_NAME

DEEPSEEK_API_KEY= settings.DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL= settings.DEEPSEEK_BASE_URL
DEEPSEEK_MODEL_NAME = settings.DEEPSEEK_MODEL_NAME


main_model_client = AsyncOpenAI(
    api_key=SF_API_KEY,
    base_url=SF_BASE_URL,
)
sub_model_client = AsyncOpenAI(
    api_key=ALI_BAILIAN_API_KEY,
    base_url=ALI_BAILIAN_BASE_URL,
)
deepseek_model_client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_BASE_URL,
)

main_model = OpenAIChatCompletionsModel(
    model = MAIN_MODEL_NAME,
    openai_client=main_model_client,
)
sub_model = OpenAIChatCompletionsModel(
    model = SUB_MODEL_NAME,
    openai_client=sub_model_client,
)
deepseek_model = OpenAIChatCompletionsModel(
    model = DEEPSEEK_MODEL_NAME,
    openai_client=deepseek_model_client,
)