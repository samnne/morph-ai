import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import StdioServerParameters

load_dotenv()

class Settings:
    CHAT_KEY = os.getenv("CHAT_KEY") or os.getenv("OPENAI_API_KEY")
    MODEL = os.getenv("OPENAI_MODEL", "gpt-6.1-sol")
    BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    API_MODE = os.getenv("OPENAI_API_MODE", "responses")
    workspace = Path()
    MEMORY = Path(__file__).parent / "memory.md"
    

    MCP_SERVERS = {
        "time": StdioServerParameters(command="uvx", args=["mcp-server-time"]),
        "fetch": StdioServerParameters(command="uvx", args=["mcp-server-fetch"]),
    }
    def __init__(self):
        self.workspace = Path()
    def set_workspace(self, ws):
        self.workspace = ws
    def get_workspace(self) -> str:
        return self.workspace

settings = Settings()