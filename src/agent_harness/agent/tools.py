from contextlib import AsyncExitStack
import os
from pathlib import Path
import subprocess

import tempfile

from mcp import ClientSession, stdio_client


from agent_harness.agent.config import WORKSPACE, MCP_SERVERS, MEMORY


def list_files() -> str:
    return "\n".join(p.name for p in WORKSPACE.iterdir()) or "(empty)"


def write_file(
    filename: str, mode: str, old_lines: str, new_lines: str
) -> tuple[str, str]:
    if not len(new_lines):
        return "No Old Lines provided", "No New Lines"

    target = Path(WORKSPACE / filename)
    tmp = tempfile.NamedTemporaryFile("w", dir=target.parent, delete=False)

    try:
        if target.exists() and len(old_lines):
            with open(target, "r") as file:
                for line in file:
                    if old_lines.lower() in line.lower():
                        tmp.write(new_lines)
                    else:
                        tmp.write(line)
        else:
            tmp.write(new_lines)

        tmp.close()
        os.chmod(tmp.name, 0o777)
        os.replace(tmp.name, target)
    except Exception:
        if os.path.exists(tmp.name):
            os.remove(tmp.name)
        raise

    return ("".join(old_lines), "".join(new_lines))


def execute_command(command: str, args: list) -> str:
    try:
        result = subprocess.run(
            [command, *args],
            capture_output=True,
            cwd=WORKSPACE,
            text=True,
            check=True
        )
        print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("Command failed with exit code:", e.returncode)
        print("Error output:\n", e.stderr)


def read_file(filename: str) -> str:
    path = WORKSPACE / filename
    if not path.is_file():
        return f"no file named: {filename}"
    return path.read_text()


mcp_sessions: dict[str, ClientSession] = {}


async def connect_mcp(stack: AsyncExitStack):
    """Launch a given mcp server"""
    for name, params in MCP_SERVERS.items():
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        tools = (await session.list_tools()).tools
        for tool in tools:
            mcp_sessions[tool.name] = session
            TOOLS_SCHEMA.append(
                {
                    "type": "function",
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                }
            )
        print(f"    [mcp] connected '{name}': {[t.name for t in tools]}")


def save_memory(fact: str):
    """APPEND one fact about the user to long-term memory"""
    with MEMORY.open("a") as f:
        f.write(f"- fact {fact}\n")
    return f"saved: {fact}"


LOCAL_TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
    "save_memory": save_memory,
    "execute_command": execute_command,
}


TOOLS_SCHEMA = [
    {
        "type": "function",
        "name": "list_files",
        "description": "List the files available in the workspace.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "execute_command",
        "description": "Executes python commands",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "the command in a users path that is executable",
                },
                "args": {
                    "type": "array",
                    "description": "the command args example, command='ls',args=['-la']",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "read_file",
        "description": "Read a file from the workspace by filename.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The name of the file to read.",
                }
            },
            "required": ["filename"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "write_file",
        "description": "Write or replace lines in a file.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The path of the file to write.",
                },
                "mode": {
                    "type": "string",
                    "description": "The file open mode.",
                },
                "old_lines": {
                    "type": "string",
                    "description": "The existing lines to replace; use an empty string to append.",
                },
                "new_lines": {
                    "type": "string",
                    "description": "The lines to write.",
                },
            },
            "required": ["filename", "mode", "old_lines", "new_lines"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "save_memory",
        "description": "Append one fact about the user to long-term memory and saves it to memory.md.",
        "parameters": {
            "type": "object",
            "properties": {
                "fact": {
                    "type": "string",
                    "description": "The fact to save.",
                }
            },
            "required": ["fact"],
            "additionalProperties": False,
        },
    },
]
