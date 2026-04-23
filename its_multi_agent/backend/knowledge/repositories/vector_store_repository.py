
from typing import List

from langchain_chroma import Chroma
from langchain_core.documents import Document

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

    def embedd_document(self, text:str) -> List[float]:
        """
        query向量化
        Args:
            text: 输入文本

        Returns: 浮点数列表

        """

        return self.embedding.embed_query(text)

    def embedd_documents(self, texts:List[str]) -> List[List[float]]:
        """
        对字符串列表向量化
        Args:
            texts:字符串列表

        Returns:

        """
        return self.embedding.embed_documents(texts)


    def search_similarity_with_score(self,user_question:str,top_k: int = 5)->List[tuple[Document, float]]:
        """
        相似性检索带文档分数
        返回的是l2距离得分 分数越小越相似，不是余弦相似度
        Args:
            user_question:

        Returns:
            List[tuple[Document,float]] 返回基于向量检索的相似性文档列表
        """
        return self.vector_database.similarity_search_with_score(user_question,top_k)
