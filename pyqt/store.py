"""Task storage, independent of the UI."""
import json
import os
from pathlib import Path
from uuid import uuid4


def data_path() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif __import__("sys").platform == "darwin":
        root = Path.home() / "Library/Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "simple-todo" / "tasks.json"


class TaskStore:
    def __init__(self, path: Path | None = None):
        self.path = path if path is not None else data_path()
        self.tasks: list[dict] = []

    def load(self):
        if not self.path.exists():
            return
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("Task data must be a list.")
        seen = set()
        for task in raw:
            if (not isinstance(task, dict)
                or not isinstance(task.get("id"), str)
                or task["id"] in seen
                or not isinstance(task.get("title"), str)
                or not task["title"].strip()
                or not isinstance(task.get("done"), bool)):
                raise ValueError("Invalid task data.")
            seen.add(task["id"])
        self.tasks = raw

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.tasks, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)

    def add(self, title: str):
        title = title.strip()
        if not title:
            raise ValueError("Please enter a task.")
        task = {"id": uuid4().hex, "title": title, "done": False}
        self.tasks.append(task)
        return task
