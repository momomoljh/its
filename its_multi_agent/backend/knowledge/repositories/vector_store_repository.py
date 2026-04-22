
from langchain_chroma import Chroma
class VectorStoreRepository:
    """
    向量数据库读写操作
    """
    def __init__(self):
        """
        创建示例
        """
        self.vector_database = Chroma()