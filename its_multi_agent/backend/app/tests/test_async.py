import asyncio


async def test():
    print("2222")
    yield 111
    print("33333")
    yield 222

async def main():
    async for test1 in test():
        print( test1)

if __name__ == "__main__":
    asyncio.run(main())

