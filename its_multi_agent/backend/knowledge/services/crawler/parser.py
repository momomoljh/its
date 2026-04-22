from typing import Dict,Any

from utils.text_utils import TextUtils


class HTMLParser:


    def parse_html_to_markdown(self,knowledge_no:int, html_data:Dict[str,Any])->str:
        """

        :param knowledge_no:
        :param html_data:
        :return:
        """
        if not html_data or not html_data['content'] :
            raise ValueError("解析数据不存在")

        items=[f"# 知识库{knowledge_no}\n"]

        html_title = html_data.get('title','暂无标题')

        items.append(f"## 标题\n{html_title.strip()}\n")

        html_digest = html_data['digest']
        if html_digest and html_digest.strip():
            items.append(f"## 问题描述\n{html_digest}\n")

        firstTopicName= html_data['firstTopicName']
        subTopicName= html_data['subTopicName']
        questionCategoryName= html_data['questionCategoryName']

        categories=[]
        if firstTopicName and firstTopicName.strip():
            categories.append(f"主分类:\n{firstTopicName.strip()}")
        if subTopicName and subTopicName.strip():
            categories.append(f"子分类:\n{subTopicName.strip()}")
        elif questionCategoryName and questionCategoryName.strip():
            categories.append(f"问题分类:\n{questionCategoryName.strip()}\n")
        if categories:
            items.append(f"## 分类\n" +"\n".join(categories) + "\n")

        html_keywords = html_data['keyWords']
        keyword_list = []
        if html_keywords:
            for keyword in html_keywords:
                if isinstance(keyword,str):
                    keyword_list.extend([keyword.strip() for keyword in keyword.split(',') if keyword.strip()])
            if keyword_list:
                keywords = ','.join(keyword_list)
                items.append(f"## 关键词\n{keywords}\n")
        metadata_data = []
        html_create_time = html_data.get('createTime')
        html_version_no = html_data.get('versionNo')
        if html_create_time and html_create_time.strip():
            metadata_data.append(f'创建时间:{html_create_time.strip()}')
        if html_version_no and html_version_no.strip():
            metadata_data.append(f'版本:{html_version_no.strip()}')
        if metadata_data:
            items.append(f"## 元信息\n" + '|'.join(metadata_data) + '\n')

        html_content = html_data.get('content')
        if html_content:
            md_content = TextUtils.html_to_markdown(html_content)
            items.append(f"## 解决方案\n{md_content}\n")

        items.append(f"<!-- 文档主题 {html_title} (知识库编号: {knowledge_no}) -->" )

        return '\n'.join(items)


