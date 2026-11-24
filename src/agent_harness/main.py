import asyncio
from contextlib import AsyncExitStack

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Center, Container, Vertical, VerticalScroll
from textual.widgets import Button, Footer, Header, Input, Static, Label

from agent_harness.agent import v0
from agent_harness.agent.config import MODEL
from agent_harness.agent.tools import TOOLS_SCHEMA

QUESTION = "Do you want to learn about Textual CSS?"


class Agent:
    def __init__(self):
        self.tools = v0.get_tools()

    async def prompt_agent(self, question: str):
        v0.chat(question)
       

LabelID = "greeting"


class Morph(App):
    CSS_PATH = "css/dom4.tcss"

    def __init__(
        self, driver_class=None, css_path=None, watch_css=False, ansi_color=None
    ):

        self.agent = Agent()

        super().__init__(driver_class, css_path, watch_css, ansi_color)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        with Vertical(id="container"):
            with VerticalScroll(id="text-container"):
                
                yield Label(
                "Welcome to MorphAI", name="MorphAi", id=LabelID, classes="question"
            )
            yield Input(placeholder="What would you like me to do?", id="prompt")

    @on(Input.Submitted, "#prompt")
    async def handle_submit(self, event: Input.Submitted) -> None:
        container = self.query_exactly_one("#text-container")
        label = Label(content=event.value)
        container.mount(label)
        event.input.clear()
        
        val = await v0.chat(event.value)
        container = self.query_exactly_one("#text-container")
        label = Label(content=val)
        container.mount(label)

    # Triggered every time the text changes
    @on(Input.Changed, "#prompt")
    def handle_change(self, event: Input.Changed) -> None:
        self.log(f"Current text: {event.value}")


def main():

    app = Morph()
    app.run()
