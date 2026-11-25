# Everyday To-do

A standalone PyQt6 desktop app. It does not modify or depend on the agent app.

**Status:** This PyQt app was built by an AI agent and is temporary. It is planned for removal in the future.
## Install and run

From the repository root, with your Python environment activated:

```sh
python -m pip install -r pyqt/requirements.txt
python pyqt/main.py
```

With uv instead:

```sh
uv run --with 'PyQt6>=6.6,<7' python pyqt/main.py
```

Requires a graphical desktop and Python 3.10+ (the parent project requires 3.13+).

## Features

- Add tasks with Enter or the Add task button; Ctrl+N focuses the entry.
- Check/uncheck tasks to complete/reopen them.
- Double-click a task or select it and click Edit to rename it.
- Search and filter by All tasks, Active, or Completed.
- Delete tasks or clear completed tasks, with confirmation.
- Automatic local saving after every change; failed saves are reported and rolled back in the UI.

Data is stored as UTF-8 JSON in your user data directory:

- Linux: `$XDG_DATA_HOME/simple-todo/tasks.json` (defaults to `~/.local/share/simple-todo/tasks.json`)
- macOS: `~/Library/Application Support/simple-todo/tasks.json`
- Windows: `%LOCALAPPDATA%/simple-todo/tasks.json`

No account or network access is needed. Saves use a temporary file and atomic replacement. If the data file is invalid, the app reports the problem and exits without overwriting it. Use one instance at a time; concurrent editing is not supported.

## Storage tests

```sh
python -m unittest discover -s pyqt -p 'test_*.py' -v
```
