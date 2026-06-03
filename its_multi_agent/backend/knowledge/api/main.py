

import uvicorn
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
from fastapi import FastAPI
from api.routers import router
def create_app():
    #创建实例
    app = FastAPI(title = "Knowledge API")
    #注册路由
    app.include_router(router=router)

    return app

if __name__ == '__main__':
    print("准备启动web服务器")
    try:
        uvicorn.run(app=create_app(), host="127.0.0.1", port=8001)
        logger.info("启动web服务器成功")
    except KeyboardInterrupt as e :
        logger.error(f"web服务器启动失败:{str(e)}")