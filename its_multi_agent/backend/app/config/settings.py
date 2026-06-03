from pydantic import Field
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import model_validator
from typing_extensions import Self

class Settings(BaseSettings):
    """
       应用配置类

       配置项会自动从以下来源读取（优先级从高到低）：
       1. 环境变量
       2. .env 文件
       3. 默认值
       """

    # ==================== AI 服务配置 ====================
    ALI_BAILIAN_API_KEY : Optional[str] = Field(None, description="阿里百炼 API key")
    ALI_BAILIAN_BASE_URL: Optional[str] = Field(default=None, description="阿里百炼 Base URL")

    SF_API_KEY: Optional[str] = Field(default=None, description="硅基流动 API Key")
    SF_BASE_URL: Optional[str] = Field(default=None, description="硅基流动 Base URL")

    OPENAI_API_KEY: Optional[str] = Field(default=None, description="openai API Key")
    OPENAI_BASE_URL: Optional[str] = Field(default=None, description="openai Base URL")

    DEEPSEEK_API_KEY: Optional[str] = Field(default=None, description="deepseek API Key")
    DEEPSEEK_BASE_URL: Optional[str] = Field(default=None, description="deepseek Base URL")

    # ==================== 模型配置 ====================

    MAIN_MODEL_NAME: Optional[str] = Field(
        default="Qwen/Qwen3-32B",
        description="主模型名称"
    )
    SUB_MODEL_NAME: Optional[str] = Field(
        default="",
        description="qwen3.6-flash"
    )
    DEEPSEEK_MODEL_NAME: Optional[str] = Field(
        default="null",
        description="deepseek-v4-pro"
    )
    # ==================== 数据库配置 ====================

    MYSQL_HOST: Optional[str] = Field(default="localhost", description="MySQL主机地址")
    MYSQL_PORT: int = Field(default=3306, description="MySQL端口")
    MYSQL_USER: Optional[str] = Field(default="root", description="MySQL用户名")
    MYSQL_PASSWORD: Optional[str] = Field(default="", description="MySQL密码")
    MYSQL_DATABASE: Optional[str] = Field(default="its_db", description="MySQL数据库名")
    MYSQL_CHARSET: str = Field(default="utf8mb4", description="MySQL字符集")
    MYSQL_CONNECT_TIMEOUT: int = Field(default=10, description="MySQL连接超时（秒）")
    MYSQL_MAX_CONNECTIONS: int = Field(default=5, description="MySQL最大连接数")

    # ==================== 外部服务配置 ====================

    # 知识库服务
    KNOWLEDGE_BASE_URL: Optional[str] = Field(
        default=None,
        description="知识库服务URL"
    )

    # 通义千问搜索服务
    DASHSCOPE_BASE_URL: Optional[str] = Field(
        default=None,
        description="通义千问 DashScope Base URL"
    )
    DASHSCOPE_API_KEY: Optional[str] = Field(
        default="sk-9464965c0c1d4d95b509babec523d048",
        description="通义千问 DashScope API Key"
    )

    # 通用搜索服务
    FIRECRAWL_URL: Optional[str] = Field(
        default=None,
        description="联网搜索 API KEY"
    )
    # 百度地图服务
    BAIDUMAP_AK: Optional[str] = Field(
        default=None,
        description="百度地图 AK (Access Key)"
    )

    # ==================== Pydantic Settings 配置 ====================

    model_config = SettingsConfigDict(
        # 计算.env文件的绝对路径：config目录的父目录(app目录)下的.env
        env_file=str(Path(__file__).parent.parent / ".env"),
        env_file_encoding="utf-8",  # .env文件编码
        case_sensitive=True,  # 环境变量名大小写敏感
        extra="ignore",  # 忽略额外的环境变量
        validate_default=True,  # 验证默认值
    )

    # ====================  ====================
    @model_validator(mode='after')
    def check_ai_service_configuration(self) -> Self:
        """
        验证器：在配置加载完成后自动执行。
        如果需要强制至少配置一个 AI 服务，可以在这里抛出 ValueError
        """
        # 注意：这里 self 已经是实例化后的模型对象
        has_service = any([
            self.SF_API_KEY and self.SF_BASE_URL,
            self.ALI_BAILIAN_API_KEY and self.ALI_BAILIAN_BASE_URL
        ])

        if not has_service:
            raise ValueError("必须配置至少一个 AI 服务 (硅基流动 或 阿里百炼)")

        return self


# 创建全局配置实例
settings = Settings()
