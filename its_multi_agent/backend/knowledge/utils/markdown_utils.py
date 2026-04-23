import os
from typing import Any, Dict, List, re

from numba.core.runtime.nrtdynmod import meminfo_data_ty


class MarkdownUtils:
    @staticmethod
    def collect_md_metadata(folder_path : str)->List[Dict[str,Any]]:
        """
        收集markdown源数据

        遍历指定目录，提取标题和路径信息
        Args:
            folder_path: markdown所在目录

        Returns:
            路径 标题列表
        """
        md_metadata = []
        if not os.path.exists(folder_path):
            return md_metadata

        filename_pattern = re.compile(r'(.+?)-(.*?)\.md')
        for filename in os.listdir(folder_path):
            if filename.endswith('.md'):
                match = filename_pattern.match(filename)
                if match:
                    title = match.group(1)
                else:
                    title = os.path.splitext(filename)[0].strip()
                md_metadata.append({
                    "path": os.path.join(folder_path, filename),
                    'title': title,
                })
        return md_metadata

    @staticmethod