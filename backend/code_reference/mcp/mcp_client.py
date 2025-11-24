import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from contextlib import AsyncExitStack
from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

#自己Build 一个 MCPClient 的Class
class MCPClient:
    def __init__(self):
        """初始化MCP客户端。Initialize the MCPClient."""
        self.exit_stack = AsyncExitStack()
        self.api_key = os.getenv("OPENAI_API_KEY", "sk-GThm2kziVpkPUMLMfCTTbvixiJKB1MB5cX73Rxs6cjN3M7u4")
        self.base_url = os.getenv("OPENAI_API_BASE", "https://xiaoai.plus/v1")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set.") 
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
    async def connect_to_server(self, server_script_path: str):
        """连接到MCP服务器。Connect to the MCP server."""
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file.")
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command,
            args=[server_script_path],
            env=None,
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )
        await self.session.initialize()
        response = await self.session.list_tools()
        tools = response.tools
        print(f"Connected to server with tools: {[tool.name for tool in tools]}")

    async def process_query(self, query: str) -> str:
        """使用大模型處理查詢並調用可用的MCP工具。Process the query and return the response."""
        messages = [
            {"role": "system", "content": "你可以使用工具來查詢天氣。"},
            {"role": "user", "content": query}
        ]

        response = await self.session.list_tools()
        available_tools = [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema  # 確保 inputSchema 是符合 OpenAI function-calling 的 JSON schema
                }
            } for tool in response.tools
        ]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=available_tools  # 用 tools 而不是 functions
        )

        content = response.choices[0]
        if content.finish_reason == "tool_calls":
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name  # 修正这里
            tool_args = json.loads(tool_call.function.arguments)
            
            result = await self.session.call_tool(tool_name, tool_args)
            print(f"Tool {tool_name} returned: {result.content[0].text}")

            messages.append(content.message.model_dump())
            messages.append({
                "role": "tool",
                "content": result.content[0].text,
                "tool_call_id": tool_call.id,
            })

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages
            )
            return response.choices[0].message.content
        return content.message.content
        
    async def chat_loop(self):
        """運行交互式聊天循環"""
        print("\n MCP客戶端已經啟動：請輸入exit退出。MCP Client is ready. Type 'exit' to quit.")
        while True:
            try:
                user_input = await self.get_user_input()
                if user_input.lower() == "exit":
                    break

                response = await self.process_query(user_input)
                print(f"Assistant: {response}")
            except Exception as e:
                print(f"Error: {e}")
        
    async def cleanup(self):
        """清理資源並關閉會話。Cleanup resources and close the session."""
        if self.session:
            await self.session.shutdown()
        await self.exit_stack.aclose()
    
    async def get_user_input(self) -> str:
        """异步获取用户输入。Get user input asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, "You: ")

async def main():
    if len(sys.argv) < 2:
        print("Usage: python mcp_client.py mcp_server.py")
        sys.exit(1)
    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    import sys
    asyncio.run(main())
