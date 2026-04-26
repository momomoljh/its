from typing import List, Any, Dict
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
import jieba
from langchain_core.documents import Document
from repositories.vector_store_repository import VectorStoreRepository, logger
from utils.markdown_utils import MarkdownUtils
from config.settings import settings
from services.ingestion.ingestion_processor import IngestionProcessor
from sklearn.metrics.pairwise import cosine_similarity
class RetrivalService:

    def __init__(self):
        self.chroma_vector = VectorStoreRepository()
        self.spilter = IngestionProcessor()

    def retrival(self,user_question:str) -> List[Document]:

        """
        核心检索方法
        Args:
            user_question: 用户输入问题

        Returns:
            返回相似文档列表 指定TOP-N
        """
        # 1路检索 向量检索
        based_vector_candidates = self._search_based_vector(user_question)

        # 2路检索
        # 粗排
        based_title_candidates = self._search_based_title(user_question)
        #合并
        total_candidates = based_title_candidates + based_vector_candidates
        #去重
        unique_candidates = self._deduplicate(total_candidates)

        #打分排序
        unique_sorted_candidates = self._reranking(unique_candidates,user_question)
        # 返回 指定top-n
        return unique_sorted_candidates

    def _search_based_vector(self,user_question:str) -> List[Document]:
        documents_with_score = self.chroma_vector.search_similarity_with_score(user_question)
        # TODO(不用距离得分)
        based_vector_candidates = []
        for documents,_ in documents_with_score:
            based_vector_candidates.append(documents)
        return based_vector_candidates


    def _search_based_title(self,user_query:str) -> List[Document]:
        mds_metadata = MarkdownUtils.collect_md_metadata(settings.CRAWL_OUTPUT_DIR)
        rough_mds_title = self.rough_ranking(user_query,mds_metadata)
        fine_mds_title = self.fine_ranking(user_query,rough_mds_title)
        #根据标题获取文档
        based_title_candidates = []
        for fine_md_metadata in fine_mds_title:
            try:
                with open(fine_md_metadata["path"],"r",encoding="utf-8") as f:
                    content = f.read()
                if len(content) < 3000:
                    doc = Document(page_content=content,metadata={
                        "title":fine_md_metadata["title"],
                        "path":fine_md_metadata["path"],
                    })
                    based_title_candidates.append(doc)
                else:
                    doc_chunks = self._deal_long_title_content(content,fine_md_metadata,user_query)
                    based_title_candidates.extend(doc_chunks)

            except Exception as e:
                logger.info(f"打开文件时失败:{e}")
                return []

        return based_title_candidates

    def rough_ranking(self, user_query, mds_metadata:List[Dict[str, Any]])-> List[Dict[str, Any]]:
        """
        基于jieba对标题分词匹配
        Args:
            user_query: 用户提问
            mds_metadata: md元数据

        Returns:
            List[Dict[str, Any]]:(标题，路径，得分)
        """
        if not mds_metadata:
            return []
        ROUGHIN_WORD_WEIGHT = 0.7
        for md_metadata in mds_metadata:
            md_metadata_title = md_metadata["title"]
            if not md_metadata_title and not md_metadata_title.strip():
                continue
            #jarcard算法 A 交 B / A 并 B
            user_query_char = set(user_query)
            mds_metadata_title_char = set(md_metadata_title)
            unique_char = user_query_char | mds_metadata_title_char
            char_score =  len(user_query_char & mds_metadata_title_char) / len(unique_char) if len(unique_char) > 0 else 0
            #jieba 因素大
            mds_metadata_title_word = set(jieba.lcut(md_metadata_title))
            user_query_word = set(jieba.lcut(user_query))
            unique_word = user_query_word | mds_metadata_title_word
            word_score = len(user_query_word & mds_metadata_title_word) / len(unique_word) if len(unique_word) > 0 else 0

            rough_score = word_score * ROUGHIN_WORD_WEIGHT + char_score * (1 - ROUGHIN_WORD_WEIGHT)

            md_metadata["roughing_score"] = float(rough_score)


        return sorted(mds_metadata, key=lambda x: x["roughing_score"], reverse=True)[:50]

    def fine_ranking(self, user_query, rough_mds_metadata:List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rough_mds_metadata:
            return []

        query_embedding = self.chroma_vector.embedd_document(user_query)

        rough_title = [md_metadata["title"] for md_metadata in rough_mds_metadata]

        rough_query_embedding = self.chroma_vector.embedd_documents(rough_title)

        similarities = cosine_similarity([query_embedding], rough_query_embedding).flatten()

        ROUGH_HEIGHT = 0.3
        FINE_HEIGHT = 0.7
        for index, md_metadata in enumerate(rough_mds_metadata):
            sim = similarities[index]
            if sim < 0:
                sim = 0
            roughing_score = md_metadata["roughing_score"]
            final_score = roughing_score * ROUGH_HEIGHT + FINE_HEIGHT * sim
            md_metadata["final_score"] = final_score
            md_metadata["sim_score"] = sim

        sim_mds_metadata = sorted(rough_mds_metadata, key=lambda x: x["final_score"], reverse=True)[:5]
        return sim_mds_metadata

    def _deal_long_title_content(self, content:str, fine_mds_title:Dict[str,Any], user_query:str)->List[Document]:
        """
        处理标题对应长文本
        Args:
            content:
            fine_mds_title:
            user_query:

        Returns:
            List[Document]
        """
        doc_chunks = self.spilter.document_spliter.split_text(content)
        doc_chunks_title = fine_mds_title["title"]
        doc_chunks_with_title = [f"文档来源:{doc_chunks_title}" for doc_chunk in doc_chunks]
        query_embedding = self.chroma_vector.embedd_document(user_query)
        doc_chunk_embeddings = self.chroma_vector.embedd_documents(doc_chunks_with_title)
        doc_chunks_similarity = cosine_similarity([query_embedding], doc_chunk_embeddings).flatten()
        top_doc_chunks_indices = doc_chunks_similarity.argsort()[-3:][::-1]
        docs = []
        for i,chunk_idx in enumerate(top_doc_chunks_indices):
            doc = Document(
                page_content= doc_chunks_with_title[chunk_idx],
                metadata= {
                    "title": fine_mds_title["title"],
                    "path": fine_mds_title["path"],
                    "chunk_index": int(chunk_idx),
                    "similarity": float(doc_chunks_similarity[chunk_idx])
                }
            )
            docs.append(doc)
        return docs

    def _deduplicate(self, total_candidates: List[Document]) -> List[Document]:
        if not total_candidates:
            return []

        seen = set()
        unique_candidates = []
        for document in total_candidates:
            key = (document.metadata["title"], document.page_content[:100])
            if key not in seen:
                seen.add(key)
                unique_candidates.append(document)
        return unique_candidates

    def _reranking(self, unique_candidates: List[Document], user_question: str) -> List[Document]:
        """
        第二路长文档已经计算，不需要再计算了
        Args:
            unique_candidates:
            user_question:

        Returns:

        """
        if not unique_candidates:
            return []
        #（document,score)
        score_doc = []
        need_embedding_docs = []
        need_embedding_candidates_indices = []
        for candidate_index, unique_candidate in enumerate(unique_candidates):
            # 判断是不是第二路长文档
            if "chunk_index" in unique_candidate.metadata and "similarity" in unique_candidate.metadata:
                score_doc.append((unique_candidate,unique_candidate.metadata['similarity']))
            else:
                need_embedding_docs.append(unique_candidate)
                need_embedding_candidates_indices.append(candidate_index)
        if need_embedding_docs:
            user_question_embedding = self.chroma_vector.embedd_document(user_question)
            embedding_doc_content = ["文档来源:" + doc.metadata["title"] + doc.page_content for doc in need_embedding_docs]
            doc_embeddings = self.chroma_vector.embedd_documents(embedding_doc_content)
            similarity = cosine_similarity([user_question_embedding], doc_embeddings).flatten()
            # 排序
            for index, candidate_index in enumerate(need_embedding_candidates_indices):
                score_doc.append((unique_candidates[candidate_index], similarity[index]))

        sorted_doc = sorted(score_doc, key=lambda x: x[1], reverse=True)

        return [doc for doc,_ in sorted_doc[:2]]



if __name__ == '__main__':
    retrival_service = RetrivalService()
    # rough_ranking_result = retrival_service.rough_ranking("电脑如何开机",MarkdownUtils.collect_md_metadata(settings.CRAWL_OUTPUT_DIR))
    # for rough_mds_metadata in rough_ranking_result[:10]:
    #     print(rough_mds_metadata)
    # fine_ranking_result  = retrival_service.fine_ranking("电脑如何开机",rough_ranking_result)
    # for fine_mds_metadata in fine_ranking_result:
    #     print(fine_mds_metadata)
    # result = retrival_service.retrival("我的电脑开机后没有任何反应")
    result = retrival_service.retrival("如何安装联想的一键影音")
    # result = retrival_service.retrival("联想手机K900常见问题汇总有哪些")
    for r in result:
        print(r)