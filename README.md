# Agent Harness (MorphAI)

A Python agent harness with a Textual terminal UI, an interactive command-line loop, local filesystem/process tools, and Model Context Protocol (MCP) integrations. The model client supports OpenAI's Responses API and OpenAI-compatible Chat Completions endpoints.

This is an early implementation. See [Current limitations](#current-limitations) for differences between the interfaces and known issues.

## Requirements

- Python 3.13 or newer.
- [uv](https://docs.astral.sh/uv/) for the commands below. The CLI also requires `uvx` on `PATH` to launch its configured MCP servers.
- Access to a hosted model API or a local OpenAI-compatible server. Tool use requires a model/server that supports function calling.

Dependencies are declared in `pyproject.toml`: `dotenv`, `mcp`, `openai`, `pydantic`, and `textual`.

## Setup

From the repository root:

```sh
uv sync
```

Before using filesystem or command tools, edit `WORKSPACE` in `src/agent_harness/agent/config.py` to point to your checkout or intended working directory. It is currently hard-coded to `/home/mashce/Work/agent_harness`; it is not inferred from your current directory or configurable through an environment variable.

Create a `.env` file in the project root, for example:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=your-model-name
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_MODE=responses
```

`.env` is ignored by Git. Do not commit credentials.

### Configuration

Environment variables are loaded with `python-dotenv`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `CHAT_KEY` | Unset | API key; takes precedence over `OPENAI_API_KEY` when nonempty. |
| `OPENAI_API_KEY` | Unset | API key when `CHAT_KEY` is not set. |
| `OPENAI_MODEL` | `gpt-6.1-sol` | Model identifier sent to the configured endpoint. Set this to a model available from your provider. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible API base URL. Include `/v1` if your server requires it. |
| `OPENAI_API_MODE` | `responses` | `responses` for the Responses API, or `chat` for Chat Completions. |

For a keyless local server, provide a placeholder key and select its model:

```dotenv
OPENAI_API_KEY=local
OPENAI_MODEL=your-local-model
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_MODE=chat
```

Make sure `CHAT_KEY` is unset if you want `OPENAI_API_KEY` to be used. Chat Completions tool execution currently has a known issue described below.

## Running

### Textual terminal UI

```sh
uv run agent-harness
# Equivalent short entry point:
uv run ah
```

Both commands launch the `Morph` Textual app, which displays a “Welcome to MorphAI” greeting and a prompt input. Submit a prompt with Enter; the UI displays your prompt and the final assistant response.

The UI uses environment-based model configuration and exposes the local tools. It does **not** currently initialize MCP connections or handle the CLI slash commands.

### Interactive CLI

```sh
uv run python -m agent_harness.agent.v0
```

This interface initializes the configured MCP servers before accepting prompts.

| Command | Action |
| --- | --- |
| `/model` | Interactively configure the provider, base URL, model, API mode, and API key. |
| `/tools` | List available local and discovered MCP tools. |
| `/quit` or `/exit` | End the session. |

The `/model` provider choices are `current`, `openai`, `local`, and `compatible`. API keys are entered without echoing and model changes apply only to the current process; they are not written to `.env`. Switching endpoints does not silently reuse the previous endpoint's key. The `local` option supplies a placeholder for keyless servers when no key is entered.

Ctrl+C or end-of-input also exits the prompt loop. The CLI needs its MCP servers to start successfully before `/model` is available.

## Tools

### Local tools

| Tool | Implementation |
| --- | --- |
| `list_files` | Lists immediate entries in the supplied directory. Relative paths use the process's current directory. |
| `read_file` | Reads a text file relative to `WORKSPACE` unless an absolute path is supplied. |
| `write_file` | Creates/overwrites a file, or replaces individual lines containing a case-insensitive match. See the caveats below. |
| `execute_command` | Runs an executable with an argument list, with `WORKSPACE` as its working directory, and captures output. This is not limited to Python commands. |
| `save_memory` | Appends a fact to `src/agent_harness/agent/memory.md`. |

**Safety:** Tools run with your user account's permissions. There is no approval step, workspace containment enforcement, or command sandbox. Only use this harness with trusted prompts and an appropriately restricted environment. Tool names and arguments are printed to the terminal and may contain sensitive data.

### MCP servers

`MCP_SERVERS` in `src/agent_harness/agent/config.py` configures two stdio servers:

- `time`: `uvx mcp-server-time`
- `fetch`: `uvx mcp-server-fetch`

The CLI starts these processes, initializes MCP sessions, discovers their tools, and adds them to the model's tool schema. MCP tool calls are routed to the corresponding session. Edit `MCP_SERVERS` to change the integrations. Initial startup may require network access for `uvx` to obtain the server packages.

## Agent flow and memory

`agent.py` creates an async OpenAI client on demand and sends a system prompt plus the user's message to the selected model. In Responses mode, it executes returned function calls, adds their results to the request history, and repeats until the model returns a final response.

Each `chat()` invocation starts a new message list: conversation history is retained within a single tool-call loop, not across separate user prompts. The UI displays previous exchanges, but does not send that transcript back to the model.

The memory helpers are intended to persist user facts in `src/agent_harness/agent/memory.md`. This is separate from `WORKSPACE`; see the current memory-loading bug below.

## Project layout

```text
pyproject.toml                       # Dependencies and agent-harness / ah entry points
src/agent_harness/
├── main.py                          # Textual app and installed entry point
├── css/dom4.tcss                     # Terminal UI styling
└── agent/
    ├── agent.py                     # Model configuration, API calls, tool-call loops
    ├── config.py                    # Environment defaults, workspace, MCP servers
    ├── tools.py                     # Local tools, schemas, MCP discovery and routing
    ├── v0.py                        # Interactive CLI and /model configuration
    ├── memory.py                    # Memory-loading helper
    └── memory.md                    # Persisted user facts
```

## Current limitations

- **Chat Completions tool results:** The `chat` API branch calls the async `_run_tool()` helper without `await`. Ordinary text responses can work, but tool-call results are not correctly resolved in that branch. The Responses branch awaits tool execution.
- **Memory loading:** The system prompt interpolates `load_memory` rather than calling `load_memory()`, so saved facts are not currently injected into the prompt.
- **File writes:** `write_file` ignores its `mode` argument. An empty `old_lines` overwrites the file rather than appending, despite the tool schema's description. Nonempty matches are replaced line by line, not as a multiline block. Parent directories must already exist, and replacement files are set to mode `0777`.
- **UI/CLI differences:** Only the CLI connects MCP servers and implements `/model`, `/tools`, and exit commands. The UI displays final responses rather than streaming tokens.
- **Error recovery:** A request exception in the CLI exits the prompt loop after printing an error, even though the message suggests using `/model` to recover. Restart the CLI to reconfigure after such a failure.
- **Execution limits:** Command execution is synchronous and has no configured timeout. The agent's tool-call loop has no configured iteration limit.
