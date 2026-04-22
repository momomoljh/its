import os.path

import requests
from config.settings import settings
from fastapi import HTTPException

from services.crawler.parser import HTMLParser
from utils.text_utils import TextUtils


class KnowledgeClient:

    @staticmethod
    def fetch_knowledge_content(knowledge_no:int) -> str:

        try:
            #定义url
            # http://iknow.lenovo.com.cn/knowledgeapi/api/knowledge/knowledgeDetails?knowledgeNo=9999
            knowledge_url = f"{settings.KNOWLEDGE_BASE_URL}/knowledgeapi/api/knowledge/knowledgeDetails"

            param = {"knowledgeNo": knowledge_no}

            response = requests.get(knowledge_url, params=param,timeout = 10)
            response.raise_for_status()

            response_dict = response.json()
            return response_dict["data"]
        except HTTPException as err:
            return HTTPException(f"发送数据库请求失败：{err}")

if __name__ == '__main__':

    knowledge_client = KnowledgeClient.fetch_knowledge_content(knowledge_no=1)
    parser = HTMLParser()
    md_content = parser.parse_html_to_markdown(1,knowledge_client)
    file_path_name = os.path.dirname(__file__)
    file_path = os.path.join(file_path_name, "test01.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

