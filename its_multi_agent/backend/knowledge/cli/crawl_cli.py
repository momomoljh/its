import os
import time
from lib2to3.fixes.fix_metaclass import find_metas
from os import times

from config.settings import settings
from services.crawler.client import KnowledgeClient
from services.crawler.parser import HTMLParser
from utils.text_utils import TextUtils
from repositories.file_repository import FileRepository

def main():

    success = 0
    fail = 0
    for i in range(1001):
        print(f"[{i+1}/1000] 获取knowledge_no:{i+1}")

        knowledge_content = KnowledgeClient.fetch_knowledge_content(knowledge_no=i + 1)

        if knowledge_content and knowledge_content['content']:

            parser = HTMLParser()

            md_content = parser.parse_html_to_markdown(i+1,knowledge_content)

            md_title = knowledge_content.get('title','无标题')

            clean_title = TextUtils.clean_filename(md_title.strip())

            if len(clean_title) > 50:
                clean_title = clean_title[:50].rstrip("_")

            file_name = f"{i+1:04d}-{clean_title}.md"

            file_path = os.path.join(settings.CRAWL_OUTPUT_DIR, file_name)

            FileRepository.save_file(md_content, file_path)
            success += 1
            print(f"{i+1} -> 保存成功:{file_name}")

        else:
            fail += 1
            print(f"{i+1} -> 暂无内容，保存失败")

        time.sleep(0.2)

    print(f"爬取完成：成功：{success}，失败：{fail}")


if __name__ == '__main__':
    main()