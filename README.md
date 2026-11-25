# MorphAI (TUI Agent Harness)

A Python AI-agent harness with a Textual terminal UI, local filesystem and command tools, and Model Context Protocol (MCP) integrations. The model client includes OpenAI Responses and OpenAI-compatible Chat Completions implementations.

This is a work in progress. The TUI is the primary interface; the older CLI and some integrations need fixes described under [Current limitations](#current-limitations).

## Requirements

- Python 3.13 or newer.
- [uv](https://docs.astral.sh/uv/), including `uvx` on `PATH` for the configured MCP servers.
- A model API key and access to a model that supports function calling, or a compatible local server.

Dependencies are declared in `pyproject.toml`, including `dotenv`, `mcp`, `openai`, `pydantic`, `pyfiglet`, `pyinstaller`, and `textual`. PyQt6 is only needed for the separate temporary desktop app.

## Setup

From the repository root:

```sh
uv sync
```

Create a `.env` file in the project root:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=your-model-name
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_API_MODE=responses
```

`.env` is ignored by Git. Do not commit credentials.

### Model configuration

Environment variables are loaded with `python-dotenv` in `agent/config.py`.

| Variable | Default | Purpose |
| --- | --- | --- |
| `CHAT_KEY` | Unset | API key; takes precedence over `OPENAI_API_KEY` when nonempty. |
| `OPENAI_API_KEY` | Unset | API key when `CHAT_KEY` is not set. |
| `OPENAI_MODEL` | `gpt-6.1-sol` | Model identifier. Set this to a model available from your provider. |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | API base URL, including `/v1` if required by your provider. |
| `OPENAI_API_MODE` | `responses` | `responses` or `chat`; see the Chat Completions limitation below. |

For a keyless local server, use a placeholder key and the server's model name:

```dotenv
OPENAI_API_KEY=local
OPENAI_MODEL=your-local-model
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_API_MODE=chat
```

Unset `CHAT_KEY` if you want `OPENAI_API_KEY` to take effect. Chat-only servers currently encounter the API-mode fallthrough bug described below.

### Workspace

The initial workspace is configured in `agent/config.py` as `settings.workspace`. It is currently hard-coded to `/home/mashce/Work/agent_harness`, not inferred from the directory where you launch the app.

Either change that setting before launch or use the TUI command:

```text
/workspace /absolute/path/to/project
```

`/ws /absolute/path/to/project` also works. The selected path appears on the button below the prompt. Workspace changes apply only to the running process and are not saved to configuration.

Use an existing absolute path without spaces: the current command parser only consumes the first space-delimited path token and does not validate that the directory exists. `~` is expanded.

## Running the terminal UI

Run from the repository root:

```sh
uv run python main.py
```

This launches the `Morph` Textual app with an ASCII logo, the Catppuccin Mocha theme, a scrollable conversation area, a multiline prompt, a workspace indicator, and an animated activity indicator.

- Type a prompt and press **Shift+Enter** to submit it.
- Agent requests run in a Textual async worker.
- Assistant responses are rendered as Markdown.
- Tool activity is shown alongside the conversation. In Responses mode, the UI displays tool names and arguments; in Chat Completions mode, it displays returned tool content.
- The app attempts to connect to MCP servers in a background worker at startup; see the lifecycle limitation below.

### TUI commands

Submit these with **Shift+Enter**:

| Command | Action |
| --- | --- |
| `/workspace PATH` or `/ws PATH` | Change the active workspace. |
| `/tools` | List local tool definitions and any discovered MCP tools. |
| `/commands` | Display command help. |

The help text spells the workspace command `/workspaces`; the current substring-based handler also accepts that spelling. `/model`, `/quit`, and `/exit` are not TUI slash commands. Use Textual's default Ctrl+Q binding to quit.

The project still declares `agent-harness` and `ah` script entries in `pyproject.toml`, but `[tool.uv] package = false` disables installing the project during `uv sync`, and the `ah` target is not a valid `module:function` entry point. Use the direct command above rather than relying on those shortcuts.

## Local tools

| Tool | Current behavior |
| --- | --- |
| `list_files` | Lists immediate directory entries. Relative paths are resolved against the process working directory, not the selected workspace. |
| `read_file` | Reads a text file relative to the selected workspace, or an absolute path. |
| `write_file` | Creates/overwrites a file or replaces lines containing a case-insensitive match. See limitations below. |
| `execute_command` | Runs an allowed executable in the selected workspace and captures its output. |
| `save_memory` | Appends a user fact to `agent/memory.md`, independently of the selected workspace. |

Command execution currently allows `ls`, `git`, `cat`, `head`, `tail`, `grep`, `find`, `tree`, `pwd`, `pytest`, `python`, and `uv`. Executables are resolved from `PATH`. Arguments containing a `..` path component are rejected. Commands have a 30-second timeout, and returned output is truncated after 10,000 characters.

**Safety:** These restrictions are not a sandbox. Allowed commands such as `python`, `uv`, and `git` can execute code, and file tools accept paths outside the selected workspace. Tools run with your user's permissions and without approval prompts. Use a restricted environment and trusted inputs. Tool names and arguments are also printed to the terminal and may contain sensitive data.

## MCP integrations

`settings.MCP_SERVERS` in `agent/config.py` configures two stdio servers:

- `time`: `uvx mcp-server-time`
- `fetch`: `uvx mcp-server-fetch`

`agent/tools.py` starts the processes, initializes sessions, discovers tools, adds their definitions to `TOOLS_SCHEMA`, and routes calls to the matching session. Initial startup may require network access for `uvx` to obtain the server packages. Edit `settings.MCP_SERVERS` to change the integrations.

The CLI holds its MCP context open for its prompt loop. The TUI currently closes its MCP context when its connection worker finishes, so discovery does not mean those tools remain usable.

## Conversation history and memory

`agent/agent.py` maintains a module-level `messages` list. User prompts, assistant messages, tool calls, and tool results accumulate across prompts in the same process. The model's tool loop continues until it returns a final response; it is not token streaming.

At module import, `load_memory()` reads `settings.MEMORY` (by default `agent/memory.md`) into the system prompt. The `save_memory` tool appends facts to that file. Newly saved facts are not automatically reloaded into the already-created system prompt.

Conversation history is not currently saved or restored between runs. `agent/memory.py` contains a `Session` data class, but session-writing code is commented out; the presence of `sessions.json` does not indicate active session persistence.

## Legacy interactive CLI

```sh
uv run python -m agent.v0
```

The CLI initializes MCP servers and provides these commands:

| Command | Action |
| --- | --- |
| `/model` | Configure provider, base URL, model, API mode, and API key for the current process. |
| `/tools` | Print local and discovered MCP tool definitions. |
| `/quit` or `/exit` | End the session. |

`/model` supports `current`, `openai`, `local`, and `compatible` providers. Keys are entered without echoing, are not saved to `.env`, and are not silently reused for a different endpoint. The local option supplies a placeholder key when needed.

**The CLI's normal prompt path is currently broken:** it uses `await chat(question)`, but `chat()` is now an async generator and must be consumed with `async for`. Slash commands are handled separately, but submitting a normal prompt raises an error and exits the loop. MCP startup must also succeed before the prompt loop becomes available.

## Project layout

```text
main.py                 # Textual app; run directly from the repository root
modals.py               # SessionModal placeholder
pyproject.toml          # Dependencies and script declarations
uv.lock                 # Dependency lockfile
agent/
├── agent.py            # Model configuration, shared history, API/tool loops
├── config.py           # Environment defaults, workspace, memory path, MCP servers
├── tools.py            # Local tools, command restrictions, MCP discovery/routing
├── v0.py               # Legacy CLI and interactive model configuration
├── memory.py           # Memory loader and session data class
├── memory.md           # Persisted user facts
└── poem.py             # Standalone helper script
config/
└── logo.py             # ASCII branding for the TUI
css/
└── dom4.tcss           # Textual styling
pyqt/                   # Temporary, independent PyQt6 to-do app
```

The checkout also contains empty `database/`, `docker/`, and `service/` directories; these are not implemented services. Generated `build/` and `dist/` directories are ignored by Git.

### Temporary PyQt app

`pyqt/` contains an independent, agent-built PyQt6 to-do application with local JSON storage and storage tests. It is **temporary and planned for removal**, not part of the MorphAI interface. See [pyqt/README.md](pyqt/README.md) for its setup and test commands. PyQt6 is not included in the main project's dependencies.

## Current limitations

- **Chat Completions fallthrough:** Tool calls are now correctly awaited in both API branches, but the `chat` branch has no return after its loop. It falls through into the Responses API loop, potentially issuing an unsupported request and mixing API-specific history formats. Prefer `responses` with a compatible provider for now.
- **CLI async-generator mismatch:** The legacy CLI awaits `chat()` rather than iterating over it, so ordinary prompts fail as described above.
- **TUI MCP lifecycle:** The connection worker exits its `AsyncExitStack` after discovery, closing the sessions while their tool definitions remain registered. Connection and response workers also share Textual's default exclusive worker group, so submitting a prompt can cancel an in-progress connection.
- **Blocking tools:** Local tool functions run synchronously inside the async agent loop. Filesystem work and command execution can still block the UI event loop even though requests run in a worker.
- **File writes:** `write_file` ignores `mode`, rejects empty `new_lines`, and overwrites rather than appends when `old_lines` is empty. Matching is case-insensitive and line-by-line, not a multiline block replacement. Parent directories must exist, and replacement files are given permissions `0777`.
- **Workspace handling:** Workspace switching does not validate paths or support paths with spaces. `list_files` does not consistently use the selected workspace: its intended `.` special case compares a `Path` with a string and is never reached.
- **Error and cancellation handling:** The TUI response worker has no explicit error cleanup for its activity indicator. New submissions use an exclusive worker and can cancel an active response. The CLI exits its prompt loop after request errors rather than offering recovery in place.
- **History and limits:** There is no conversation reset command, history trimming, active session persistence, or configured tool-loop iteration limit.
