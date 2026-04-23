from typing import List, Any, Dict

import jieba
from langchain_core.documents import Document
from repositories.vector_store_repository import VectorStoreRepository
from utils.markdown_utils import MarkdownUtils
from config.settings import Settings
from sklearn.metrics.pairwise import cosine_similarity
class RetrivalService:

    def __init__(self):
        self.chroma_vector = VectorStoreRepository()

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

        #去重


        #打分排序

        # 返回 指定top-n


    def _search_based_vector(self,user_question:str) -> List[Document]:
        documents_with_score = self.chroma_vector.search_similarity_with_score(user_question)
        # TODO(不用距离得分)
        based_vector_candidates = []
        for documents,_ in documents_with_score:
            based_vector_candidates.append(documents)
        return based_vector_candidates


    def _search_based_title(self,user_query:str) -> List[Document]:
        mds_metadata = MarkdownUtils.collect_md_metadata(Settings.CRAWL_OUTPUT_DIR)
        rough_mds_title = self.rough_ranking(user_query,mds_metadata)
        fine_mds_title = self.fine_ranking(user_query,rough_mds_title)




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
        for mds_metadata in mds_metadata:
            md_metadata_title = mds_metadata["title"]
            if not md_metadata_title and not md_metadata_title.strip():
                continue
            #jarcard算法 A 交 B / A 并 B
            user_query_char = set(user_query)
            mds_metadata_title_char = set(md_metadata_title)
            unique_char = user_query_char | mds_metadata_title_char
            char_score =  len(user_query_char & mds_metadata_title_char) / len(unique_char) if len(unique_char) > 0 else 0
            #jieba 因素大
            mds_metadata_title_word = jieba.lcut(md_metadata_title)
            user_query_word = jieba.lcut(user_query)
            unique_word = user_query_word | mds_metadata_title_word
            word_score = len(user_query_word & mds_metadata_title_word) / len(unique_word) if len(unique_word) > 0 else 0

            rough_score = word_score * ROUGHIN_WORD_WEIGHT + char_score * (1 - ROUGHIN_WORD_WEIGHT)

            mds_metadata["roughing_score"] = float(rough_score)


        return sorted(mds_metadata, key=lambda x: x["roughing_score"], reverse=True)[:50]

    def fine_ranking(self, user_query, rough_mds_metadata:List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not rough_mds_metadata:
            return []

        query_embedding = self.chroma_vector.embedd_document(user_query)

        rough_title = [md_metadata["title"] for md_metadata in rough_mds_metadata]

        rough_query_embedding = self.chroma_vector.embedd_documents(rough_title)

        similarities = cosine_similarity(query_embedding, rough_query_embedding).flatten()

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