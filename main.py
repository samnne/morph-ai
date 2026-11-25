import asyncio
from contextlib import AsyncExitStack
from time import sleep

from textual import events, on, work
from textual.app import App, ComposeResult
from textual.containers import Center, Container, Horizontal, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import (
    Button,
    Footer,
    Header,
    Input,
    Markdown,
    Static,
    Label,
    TextArea,
)
from config.logo import logo
from agent import v0
from agent.config import settings
from agent.tools import TOOLS_SCHEMA, change_workspace

QUESTION = "Do you want to learn about Textual CSS?"


class Agent:
    def __init__(self):
        self.tools = v0.get_tools()


LabelID = "greeting"


class Submitted(Message):
    """Custom event carrying text data."""

    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class Morph(App):
    CSS_PATH = "css/dom4.tcss"

    def __init__(
        self, driver_class=None, css_path=None, watch_css=False, ansi_color=None
    ):

        self.agent = Agent()

        super().__init__(driver_class, css_path, watch_css, ansi_color)

    def compose(self) -> ComposeResult:
        ascii_text = logo
        self.box = [Static(classes="loader", id=f"id{i}") for i in range(5)]

        yield Header()
        yield Footer()
        with Vertical(id="container"):
            with VerticalScroll(id="text-container"):
                yield Label(ascii_text, name="Morph", id=LabelID, classes="question")

            with Vertical(id="bottom-dock"):
                yield TextArea(placeholder="What are we working on today? shift+enter to submit prompt", id="prompt")
                yield Button(label=settings.workspace.__str__(), id="ws-button")
                with Horizontal(id="loader"):
                    for i in range(5):
                        yield self.box[i]
        self.connect_mcp()

    def on_mount(self):
        self.theme = "catppuccin-mocha"

    @work(exclusive=True)
    async def connect_mcp(self) -> None:
        async with AsyncExitStack() as stack:
            await v0.connect_mcp(stack)
        
    @work(exclusive=True)
    async def stream_agent_response(self, query: str) -> None:
        """Runs concurrently in a Textual worker so the UI remains interactive."""
        container = self.query_exactly_one("#text-container", VerticalScroll)

        async for val in v0.chat(query):
            if isinstance(val, str):

                clean_val = val.replace("\\n", "\n")
                md_text = f"**[Response]**\n\n{clean_val}"
                widget = Markdown(md_text)
                await container.mount(widget)
                container.scroll_end(animate=False)

            elif isinstance(val, dict):
                output, content = val.get("output"), val.get("content")
                tool_name = val.get("tool", "")
                args = val.get("args", "")

                if output:

                    md_text = f"`(Tool) {tool_name}`: `{args}`"
                    widget = Markdown(md_text, classes="not-text")
                    await container.mount(widget)
                    container.scroll_end(animate=False)
                    continue

                if content:
                    md_text = f"`(Tool) {tool_name}`: {content}"
                    widget = Markdown(md_text, classes="not-text")
                    await container.mount(widget)
                    container.scroll_end(animate=False)
        self.post_message(Submitted("Done"))

    @work(exclusive=True, group="box_anim")
    async def animate_boxes(self, message: str) -> None:
        if message == "Done":
            for i in range(5):
                self.box[i].styles.animate(
                    "opacity", value=0.0, delay=i * 0.1, duration=1.0
                )
        while message == "Animate":
            # Fade out wave (takes 0.4s delay + 1.0s duration = 1.4s total)
            for i in range(5):
                self.box[i].styles.animate(
                    "opacity", value=0.0, delay=i * 0.1, duration=1.0
                )
            await asyncio.sleep(1.4)

            # Fade in wave
            for i in range(5):
                self.box[i].styles.animate(
                    "opacity", value=1.0, delay=i * 0.1, duration=1.0
                )
            await asyncio.sleep(1.4)

    @on(Submitted)
    def handle_submitted(self, message: Submitted) -> None:
        if message.text == "Animate":
            self.animate_boxes(message.text)
        else:
            self.animate_boxes("Done")
            self.workers.cancel_group(self, "box_anim")

    def print_tools(self):
        container = self.query_exactly_one("#text-container", VerticalScroll)
        for tool in TOOLS_SCHEMA:
            label = Label(f" [tool] {tool["name"]} - {tool["description"]}")
            container.mount(label)
    def print_commands(self):
        container = self.query_exactly_one("#text-container", VerticalScroll)
        print("All commands available in this TUI")
        commands = [
            ("/workspaces or /ws", "Change the current workspace."),
            ("/tools", "List the available tools."),
            ("/commands", "List available commands."),
        ]
        for name, description in commands:
            label = Label(f"{name} - {description}")
            container.mount(label)
        container.scroll_end(animate=False)
    
    @on(events.Key)
    async def handle_submit(self, event: events.Key) -> None:
        if event.key == "shift+enter":
            prompt: TextArea = self.query_exactly_one("#prompt")
            query = prompt.text.strip()
            prompt.clear()
            if "/workspace" in query or "/ws" in query:
                result = change_workspace(query)
                if not result:
                    self.notify(
                        f"Provide a valid workspace after /workspace path/to/workspace"
                    )
                    # handle
                    return

                button = self.query_exactly_one("#ws-button", Button)
                self.notify(f"Workspace changed to {settings.workspace}")
                button.label = settings.workspace.__str__()
               
                return
            if query.lower() == "/tools":
                self.print_tools()
                
                return
            if query.lower() == "/commands":
                self.print_commands()
                
                return

            self.post_message(Submitted("Animate"))

            if not query:
                return

            event.prevent_default()

            container = self.query_exactly_one("#text-container", VerticalScroll)
            user_label = Label(content=query)
            await container.mount(user_label)
            container.scroll_end(animate=False)

           

            self.stream_agent_response(query)

    # Triggered every time the text changes
    @on(TextArea.Changed, "#prompt")
    def handle_change(self, event: TextArea.Changed) -> None:
        self.log(f"Current text: {event.text_area.text}")


def main():

    app = Morph()
    app.run()


if __name__ == "__main__":
    main()
