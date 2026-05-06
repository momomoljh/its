from mcp.server.fastmcp import FastMCP
import uvicorn
mcp = FastMCP("demo-server")

# 1. 创建 Server，注意这里并没有直接 run()，而是准备挂载
mcp = FastMCP("远程计算服务")

@mcp.tool()
def add(a: int, b: int) -> int:
    """计算两个数字的和"""
    print(f"Server Log: 收到请求 add({a}, {b})")
    return a + b

@mcp.tool()
def echo_message(msg: str) -> str:
    """回显消息（测试网络延迟用）"""
    return f"服务端收到: {msg}"

if __name__ == "__main__":
    print("HTTP MCP Server 正在启动，监听 http://localhost:8000")
    mcp.run(transport="streamable-http")