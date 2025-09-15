# file_server.py
import asyncio
import json
from mcp.server import Server, stdio_server
from mcp.types import Tool, ToolRequest, ToolResponse, TextContent

server = Server("local-file-server")

# Register a tool
@server.tool("read_file", description="Read the contents of a local file")
async def read_file(request: ToolRequest) -> ToolResponse:
    filepath = request.arguments.get("path")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        return ToolResponse(content=[TextContent(type="text", text=content)])
    except Exception as e:
        return ToolResponse(content=[TextContent(type="text", text=f"Error: {str(e)}")])

async def main():
    async with stdio_server(server):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())