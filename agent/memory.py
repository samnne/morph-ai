from dataclasses import asdict, dataclass
import json

from agent.config import settings

def load_memory() -> str:
    if settings.MEMORY.is_file():
        return settings.MEMORY.read_text()
    return "(nothing saved yet)"
@dataclass
class Session:
    id: str
    messages: list
    def __init__(self, id: str, messages: list):
        self.id = id
        self.messages = messages
# def save_sessions(session: object):
#     id = session["id"]
#     messages = session["messages"]
#     new_session = Session(id, messages)
#     with open("sessions.json", "w") as file:
#         json.dump(asdict(new_session), file, indent=4)
    
    
    