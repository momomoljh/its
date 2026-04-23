from logging import exception
from langchain_chroma import Chroma
from config.settings import settings
from langchain_openai.embeddings import OpenAIEmbeddings
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class VectorStoreRepository:
    """
    向量数据库读写操作
    """
    def __init__(self):
        self.embedding = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.API_KEY,
            openai_api_base=settings.BASE_URL,
        )
        """
        创建向量数据库实例
        """
        self.vector_database = Chroma(
            persist_directory=settings.VECTOR_STORE_PATH,
            collection_name="ist-knowledge",
            embedding_function=self.embedding,
        )

    def add_documents(self, documents: list, batch_size: int = 16) -> int:
        """
        切分后文档保存
        Args:
            documents: chunk后文档
            batch_size: 分批次保存文档快大小

        Returns:    保存文档块数量
        """
        total_documents_chunk = len(documents)
        documents_chunk_added = 0
        try:
            for i in range(0,total_documents_chunk,batch_size):
                bath = documents[i:i+batch_size]
                self.vector_database.add_documents(bath)
                documents_chunk_added += len(bath)
                logger.info(f"成功将文档块{documents_chunk_added}/{total_documents_chunk}保存到向量数据库")
                return documents_chunk_added
        except Exception as e:
            logger.error(f"文档块列表：{documents}保存到向量数据库失败:{str(e)}")
            raise e



