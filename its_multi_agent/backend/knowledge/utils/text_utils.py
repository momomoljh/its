from markdownify import markdownify as md
from bs4 import BeautifulSoup,Tag
import re
class TextUtils:
        @staticmethod
        def html_to_markdown(html_content: str) -> str:
            if not html_content:
                return ""
            soup = BeautifulSoup(html_content, "html.parser")
            #移除无用的标签 噪音
            # script style
            for tag in soup(["script","style","noscript"]):
                tag.decompose()
            #移除广告或无用元素
            for ad in soup.select(".mceNonEditable"):
                ad.decompose()
            #合并相临加粗标签
            blog_togs = soup.findAll(['strong','b'])
            for tag in blog_togs:
                if not tag.parent:
                    continue
                next_sibling = tag.nextSibling
                if next_sibling and isinstance(next_sibling, Tag) and next_sibling.name == tag.name:
                    tag.extend(next_sibling.contents)
                    next_sibling.decompose()
            cleaned_html = str(soup)
            markdown = md(cleaned_html)
            return markdown

        @staticmethod
        def clean_filename(filename: str) -> str:
            if not filename:
                return "untitle"
            illegal_chars = r'[\\/*?:"<>|]'
            return re.sub(illegal_chars, "-", filename)


