import asyncio

from langchain_community.vectorstores.hanavector import default_table_name


def test1():
    return 1+1
async def test2():
    # 耗时操作 await
    # 操作
    #操作
    return 1+1



if __name__ == '__main__':
    # print(test2()) python函数 加上async 运行完得到协程对象 协程对象放到循环事件中 强烈建议加上await 有await一定要有async
    asyncio.run(test2())
