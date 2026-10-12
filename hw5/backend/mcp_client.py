from pathlib import Path
from typing import Any
import json

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER = Path(__file__).resolve().parent.parent / "mcp_server" / "server.py"
PYTHON = Path(r"C:\Users\sarah\OneDrive\Desktop\AI Foundations\.venv\Scripts\python.exe")


class MCPGateway:
    """The only shop-data gateway used by the agents."""

    async def __aenter__(self):
        self._stdio = stdio_client(StdioServerParameters(command=str(PYTHON), args=[str(SERVER)]))
        read, write = await self._stdio.__aenter__()
        self._session = ClientSession(read, write)
        await self._session.__aenter__()
        await self._session.initialize()
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        await self._session.__aexit__(exc_type, exc, traceback)
        await self._stdio.__aexit__(exc_type, exc, traceback)

    async def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        result = await self._session.call_tool(name, arguments)
        if result.structuredContent:
            return result.structuredContent
        if result.content and hasattr(result.content[0], "text"):
            try:
                return json.loads(result.content[0].text)
            except json.JSONDecodeError:
                return {"ok": False, "error": result.content[0].text}
        return {}
