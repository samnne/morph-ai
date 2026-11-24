import json
from dataclasses import dataclass, field
from urllib.parse import urlparse

from mcp import StdioServerParameters
from openai import AsyncOpenAI

from agent_harness.agent.memory import load_memory
from agent_harness.agent.config import API_MODE, BASE_URL, CHAT_KEY, MODEL, MCP_SERVERS
from agent_harness.agent.tools import (
    LOCAL_TOOLS,
    TOOLS_SCHEMA,
    mcp_sessions,
)


@dataclass(frozen=True)
class ModelConfig:
    model: str
    base_url: str
    api_mode: str
    api_key: str | None = field(default=None, repr=False)


_model_config = ModelConfig(MODEL, BASE_URL, API_MODE, CHAT_KEY)
client: AsyncOpenAI | None = None


def get_model_config() -> ModelConfig:
    return _model_config


def configure_model(
    model: str, api_key: str, base_url: str, api_mode: str = "responses"
) -> None:
    """Switch the active model for this process without saving credentials."""
    global _model_config, client
    model, base_url = model.strip(), base_url.strip().rstrip("/")
    if not model:
        raise ValueError("A model name is required.")
    url = urlparse(base_url)
    if url.scheme not in {"http", "https"} or not url.netloc:
        raise ValueError("Base URL must be an http(s) URL, including /v1 if required.")
    if api_mode not in {"responses", "chat"}:
        raise ValueError("API mode must be 'responses' or 'chat'.")
    if not api_key.strip():
        raise ValueError(
            "An API key is required (use a placeholder for keyless servers)."
        )

    new_client = AsyncOpenAI(api_key=api_key.strip(), base_url=base_url)
    old_client = client
    _model_config = ModelConfig(model, base_url, api_mode, api_key.strip())
    client = new_client
    if old_client is not None:
        old_client.close()


def _get_client() -> AsyncOpenAI:
    global client
    if client is None:
        if not _model_config.api_key:
            raise ValueError("No API key configured. Type /model to set up a model.")
        client = AsyncOpenAI(
            api_key=_model_config.api_key, base_url=_model_config.base_url
        )
    return client


async def _run_tool(name: str, arguments: str) -> str:
    args = json.loads(arguments or "{}")
    print(f" [tool] {name}({args})")
    if name in LOCAL_TOOLS:
        return str(LOCAL_TOOLS[name](**args))
    result = await mcp_sessions[name].call_tool(name, args)
    return "\n".join(c.text for c in result.content if hasattr(c, "text"))


async def chat(user_message: str):
    SYSTEM_PROMPT = f"""
You are a helpful assistant

Here is what you know about the user:
{load_memory}

Remember to save a fact you find out about a user and use the save_memory tool which saves it into a memory.md in the current workspace save_memory will write to the file for you 
"""
    active_client = _get_client()
    config = get_model_config()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    if config.api_mode == "chat":
        # Most local OpenAI-compatible servers implement Chat Completions,
        # rather than the newer Responses API. Both paths retain tool calls.
        tools = [
            {
                "type": "function",
                "function": {k: v for k, v in tool.items() if k != "type"},
            }
            for tool in TOOLS_SCHEMA
        ]
        while True:
            response = await active_client.chat.completions.create(
                model=config.model, messages=messages, tools=tools
            )
            message = response.choices[0].message
            assistant_message = {"role": "assistant", "content": message.content}
            if message.tool_calls:
                assistant_message["tool_calls"] = [
                    call.model_dump(exclude_none=True) for call in message.tool_calls
                ]
            messages.append(assistant_message)
            if not message.tool_calls:
                return message.content or ""
            for call in message.tool_calls:
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": _run_tool(
                            call.function.name, call.function.arguments
                        ),
                    }
                )

    while True:
        response = await active_client.responses.create(
            model=config.model,
            input=messages,
            tools=TOOLS_SCHEMA,
        )

        # Keep all output items so the model retains its reasoning state.
        messages.extend(response.output)
        tool_calls = [item for item in response.output if item.type == "function_call"]
        if not tool_calls:
            return response.output_text or ""

        for call in tool_calls:
            messages.append(
                {
                    "type": "function_call_output",
                    "call_id": call.call_id,
                    "output": await _run_tool(call.name, call.arguments),
                }
            )
