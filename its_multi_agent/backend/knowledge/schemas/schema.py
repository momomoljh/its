from pydantic import BaseModel


class UploadResponse(BaseModel):
    """
    上传文件数据响应模型
    """
    status: str
    message: str
    file_name: str
    chunks_added: int