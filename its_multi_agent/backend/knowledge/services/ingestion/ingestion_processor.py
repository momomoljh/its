import os

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from repositories.vector_store_repository import VectorStoreRepository
from langchain_community.vectorstores.utils import filter_complex_metadata
from utils.markdown_utils import MarkdownUtils
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class IngestionProcessor:
    """
    文档摄入类 :加载 切分 存储
    """
    def __init__(self):
        self.vector_store = VectorStoreRepository()
        self.document_spliter = RecursiveCharacterTextSplitter(
            chunk_size=1500,
            chunk_overlap=200,
            separators= [
                "\n##",
                "\n**",
                "\n\n",
                "\n",
                " ",
                ""
            ]
        )
    def ingest_file(self, md_path: str ) -> int:
        """
        文件完整操作
        Args:
            md_path: 路径

        Returns:
            保存文档数
        """

        #1. 获取文档列表
        # a 文档加载器 MarkDownLoader 文本加载器 TextLoader
        try:
            text_loader = TextLoader(file_path=md_path,encoding="utf-8")
            # b 加载文件返回文档列表 有且只有一个
            documents = text_loader.load()
        except Exception as e:
            logger.error(f"文件{md_path}没有加载到 原因：{str(e)}")
            raise Exception(f"文件{md_path}没有加载到 原因：{str(e)}")
        for document in documents:
            document.metadata["title"] = MarkdownUtils.extract_title(md_path)
        #2. 切分文档块列表 1.防止token限制 2.内容过多 噪音 -> 上下文参考不准确 回复质量低 (2次对chunk降噪(1.只提取 2.总结 )  利用嵌入模型二次优化chunk)
        #检索尽量多路召回(改写查询).... 1.
        #去重
        #压缩（降噪）
        #动态切分
        final_documents_chunks = []
        for doc in documents:
            if len(doc.page_content) < 3000:
                final_documents_chunks.append(doc)
            else:
                document_chunks_lists = self.document_spliter.split_documents(documents)
                for document_chunk in document_chunks_lists:

                    # 1.获取每一个文档块的标题
                    md_path = document_chunk.metadata['source']

                    title = os.path.basename(md_path)
                    document_chunk.page_content = f"文档来源:{title}\n{document_chunk.page_content}"
                final_documents_chunks.extend(document_chunks_lists)
        #切分后文档块向量数据库支持校验
        clean_documents_chunks = filter_complex_metadata(final_documents_chunks)
        #合法性校验
        valid_documents_chunks = [document for document in clean_documents_chunks if document.page_content.strip()]

        if not valid_documents_chunks:
            logger.error("切分后没有任何内容")
            return 0

        #3. 存储文档块
        total_documents_chunks= self.vector_store.add_documents(valid_documents_chunks)

        return total_documents_chunks

if __name__ == '__main__':
    # text_loader = TextLoader(file_path="C:\\Users\\Administrator\\Desktop\\0004-开机之后无任何反应怎么办？.md",encoding="utf-8")
    # # b. 加载文件返回文档列表(TextLoader返回的文档列表中有且只有一个文档对象)
    # documents = text_loader.load()
    # for doc  in documents:
    #     print(doc.page_content)

    # from langchain_community.document_loaders import UnstructuredMarkdownLoader

    # loader = UnstructuredMarkdownLoader(
    #     "C:\\Users\\Administrator\\Desktop\\0004-开机之后无任何反应怎么办？.md",
    #     mode="single",
    #     strategy="fast",
    # )
    # docs = loader.load()
    # print(docs[0].metadata)
    # print(docs[0].page_content)

    ingest_processor=IngestionProcessor()

    ingest_processor.ingest_file("C:\\Users\\86133\\PycharmProjects\\its\\its_multi_agent\\backend\\knowledge\\data\\crawl\\0001-如何使用U盘安装Windows 7操作系统.md")
    # ingest_processor.ingest_file("C:\\Users\\Administrator\\Desktop\\0188-手机、平板上的画面能无线传输到电视上播放吗？.md")

