from agent_harness.agent.config import MEMORY

def load_memory() -> str:
    if MEMORY.is_file():
        return MEMORY.read_text()
    return "(nothing saved yet)"

