import asyncio
from contextlib import AsyncExitStack
from getpass import getpass

from agent_harness.agent.config import MODEL

from agent_harness.agent.tools import TOOLS_SCHEMA, connect_mcp

from agent_harness.agent.agent import chat, configure_model, get_model_config



def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{label}{suffix}: ").strip() or default


def model_command() -> None:
    """Interactively configure a hosted or local OpenAI-compatible model."""
    current = get_model_config()
    print(f"Current model: {current.model} ({current.base_url}, {current.api_mode})")
    print("Keys are hidden and kept only for this session. Ctrl+C cancels.")
    try:
        provider = _prompt(
            "Provider (current/openai/local/compatible)", "current"
        ).lower()
        if provider not in {"current", "openai", "local", "compatible"}:
            raise ValueError("Choose current, openai, local, or compatible.")

        default_url = {
            "current": current.base_url,
            "openai": "https://api.openai.com/v1",
            "local": "http://localhost:11434/v1",
            "compatible": "",
        }[provider]
        base_url = _prompt("Base URL (include /v1 if required)", default_url).rstrip(
            "/"
        )
        same_endpoint = base_url == current.base_url.rstrip("/")
        model = _prompt("Model name", current.model if same_endpoint else "")
        default_mode = "responses" if provider == "openai" else "chat"
        if provider == "current":
            default_mode = current.api_mode
        api_mode = _prompt("API mode (responses/chat)", default_mode).lower()

        # Never silently reuse a hosted key for a different server.
        existing_key = current.api_key if same_endpoint else None
        if provider == "local":
            key_hint = (
                "Enter to keep existing key"
                if existing_key
                else "Enter for keyless server"
            )
            api_key = (
                getpass(f"API key ({key_hint}): ").strip() or existing_key or "local"
            )
        else:
            key_hint = " (Enter to keep existing key)" if existing_key else ""
            api_key = getpass(f"API key{key_hint}: ").strip() or existing_key or ""

        configure_model(model, api_key, base_url, api_mode)
        print(f"Using {model} via {api_mode} at {base_url}.\n")
    except KeyboardInterrupt:
        print("\nModel change cancelled.\n")
    except ValueError as exc:
        print(f"Model not changed: {exc}\n")

def print_tools():
    for tool in TOOLS_SCHEMA:
        print(f" [tool] {tool["name"]} - {tool["description"]}")
    
def get_tools():
    return TOOLS_SCHEMA


async def main() -> None:
    print("Type /model to configure a model, or /quit to exit.")
    async with AsyncExitStack() as stack:
        await connect_mcp(stack)
        print(f"Morph assistent ({MODEL}) with {len(TOOLS_SCHEMA)} tools - ctrl+c to quit")
        try:
            while True:
                question = input("prompt > ").strip()
                if not question:
                    continue
                if question.lower() in {"/quit", "/exit"}:
                    break
                if question.lower() == "/model":
                    model_command()
                    continue
                # if question.lower() == "/models":
                #     get_models()
                #     continue
                if question.lower() == "/tools":
                    print_tools()
                    continue
                if question.startswith("/"):
                    print("Unknown command. Use /model or /quit.\n")
                    continue
                print(f"assistant > {await chat(question)}\n")
        except (EOFError, KeyboardInterrupt):
            return 
        except Exception as exc:
                # A bad key or unavailable endpoint should not prevent /model recovery.
                print(f"Error: {exc}\nType /model to review your model settings.\n")
        print("\nBye")


if __name__ == "__main__":
    asyncio.run(main())
