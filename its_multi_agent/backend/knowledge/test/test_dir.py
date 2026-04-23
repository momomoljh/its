

from services.ingestion.ingestion_processor import IngestionProcessor
from repositories.file_repository import FileRepository
from config.settings import settings
from tqdm import tqdm
import time
def main():
    file_repository = FileRepository()

    file_path = file_repository.list_files(settings.CRAWL_OUTPUT_DIR)

    print(f"扫描到指定目录下的文件数：{len(file_path)}")

    unique_files_path = file_repository.remove_duplicate_files(file_path)

    print(f"扫描到指定目录下的唯一文件数:{len(unique_files_path)}")

    ingestion_processor = IngestionProcessor()
    success = 0
    fail = 0
    start_time = time.time()
    with tqdm(unique_files_path,desc="知识库的上传进度统计") as pbar:
        for unique_file_path in pbar:
            try:
                ingestion_processor.ingest_file(unique_file_path)
                success += 1
            except Exception as e:
                fail += 1
            finally:
                pbar.set_postfix({"success": success, "fail": fail})
    end_time = time.time()

    total_time = end_time - start_time
    print(f"最终入库的结果:成功{success}----->失败{fail}")
    print(f"最终入库成功的耗时{total_time:.2f}")

if __name__ == '__main__':
    main()