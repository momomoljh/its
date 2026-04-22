from pydantic_settings import BaseSettings,SettingsConfigDict
import os

class Settings(BaseSettings):
    API_KEY: str = os.environ.get("API_KEY")
    BASE_URL: str = os.environ.get("BASE_URL")
    MODEL: str = os.environ.get("MODEL")
    EMBEDDING_MODEL: str = os.environ.get("EMBEDDING_MODEL")

    KNOWLEDGE_BASE_URL: str = os.environ.get("KNOWLEDGE_BASE_URL")

    _current_dir = os.path.abspath(os.path.dirname(__file__))

    _project_dir = os.path.dirname(_current_dir)

    VECTOR_STORE_PATH: str = os.path.join(_project_dir,"chroma_kb")

    CRAWL_OUTPUT_DIR: str = os.path.join(_project_dir,"data","crawl")

    MD_FOLDER_PATH: str = CRAWL_OUTPUT_DIR

    CHUNK_SIZE: int = 3000
    CHUNK_OVERLAP: int = 200

    TOP_ROUGH: int = 50
    TOPFINAL: int = 5

    model_config = SettingsConfigDict(
        env_file=os.path.join(_project_dir,".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()