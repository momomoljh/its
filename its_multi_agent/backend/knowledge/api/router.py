import os.path
import logging
import shutil
from fileinput import filename

import aiofiles
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from fastapi import APIRouter, File, UploadFile, HTTPException
from schemas.schema import UploadResponse
from repositories.file_repository import FileRepository
import tempfile
from config.settings import Settings
from fastapi.concurrency import run_in_threadpool
from services.ingestion.ingestion_processor import IngestionProcessor
router = APIRouter()
file_repository = FileRepository()
ingestion_processor = IngestionProcessor()
@router.post("/upload", response_model=UploadResponse,summary="知识库摘要上传")
async def upload_file(file: UploadFile = File(...)):
    try:
        tmp_md_dir = Settings.TMP_MD_FOLDER_PATH
        file_suffix = os.path.split(file.filename)[1]
        tmp_md_path = os.path.join(tmp_md_dir, file.filename)
        if not(os.path.exists(tmp_md_path)):
            os.makedirs(tmp_md_dir,exist_ok=True)
        async with aiofiles.tempfile.NamedTemporaryFile(delete=False,suffix=file_suffix) as temp_file:
            while content:= await file.read(1024 * 1024):
                await temp_file.write(content)
            temp_file_path = temp_file.name

        shutil.move(temp_file_path, tmp_md_path)
        # chunks_added = ingestion_processor.ingest_file(temp_file_path)
        # TODO 去重
        chunks_added = await run_in_threadpool(ingestion_processor.ingest_file, tmp_md_path)
        return UploadResponse(
            status = "success",
            message = "文档上传知识库成功",
            file_name=file.filename,
            chunks_added = chunks_added,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传到知识库失败:{str(e)}")
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logger.info(f"临时文件：:{temp_file_path}已删除")


