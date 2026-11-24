import os
from pathlib import Path

from dotenv import load_dotenv
from mcp import StdioServerParameters

load_dotenv()

CHAT_KEY = os.getenv("CHAT_KEY") or os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-6.1-sol")
BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
API_MODE = os.getenv("OPENAI_API_MODE", "responses")
WORKSPACE = Path("/home/mashce/Work/agent_harness")
MEMORY = Path(__file__).parent / "memory.md"


MCP_SERVERS = {
    "time": StdioServerParameters(command="uvx", args=["mcp-server-time"]),
    "fetch": StdioServerParameters(command="uvx", args=["mcp-server-fetch"]),
}