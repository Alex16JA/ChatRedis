from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Static
from textual.message import Message
from textual import work
import redis


class Conversation(Widget):

    def __init__(self):
        super().__init__()
        self.messages = []
        self.redis_client = redis.StrictRedis(host="localhost", port=6379, db=0)
        self.channel = "canal1"
        self.subscriber = self.redis_client.pubsub()
        self.subscriber.subscribe(self.channel)

    def clear(self):
        self.messages = []

    def change_channel(self, new_channel):
        if new_channel == self.channel:
            return False

        self.subscriber.unsubscribe(self.channel)
        self.channel = new_channel
        self.subscriber.subscribe(self.channel)
        return True

    def compose(self):
        yield Static("Test")

    async def send(self, message):
        self.redis_client.publish(self.channel, message)
        return message


class FocusableContainer(Container, can_focus=True):  # type: ignore[call-arg]
    """Focusable container widget."""


class MessageBox(Widget, can_focus=True):  # type: ignore[call-arg]
    """Box widget for the message."""

    def __init__(self, text: str, role: str) -> None:
        self.text = text
        self.role = role
        super().__init__()

    def compose(self) -> ComposeResult:
        """Yield message component."""
        yield Static(self.role + self.text)


class ChatApp(App):
    """Chat app."""

    TITLE = "chat"
    SUB_TITLE = "Une super application de chaqt"

    BINDINGS = [
        Binding("q", "quit", "Quit", key_display="Q / CTRL+C"),
        ("ctrl+x", "clear", "Clear"),
    ]

    CSS_PATH = "styles.css"

    class Received(Message):
        def __init__(self, msg):
            super().__init__()
            self.message = msg

    def compose(self) -> ComposeResult:
        """Yield components."""
        yield Header()
        with FocusableContainer(id="conversation_box"):
            yield MessageBox(
                "Super application de chat!!",
                "INFO : ",
            )
        with Horizontal(id="input_box"):
            yield Input(placeholder="Écrivez votre message", id="message_input")
            yield Button(label="Envoyer", variant="success", id="send_button")
        yield Footer()

    def __init__(self):
        super().__init__()
        self.conversation = Conversation()
        self.user_name = "Anonyme"

    def on_mount(self) -> None:
        """Start the conversation and focus input widget."""
        self.listen()
        self.query_one(Input).focus()

    async def action_clear(self) -> None:
        self.conversation.clear()
        conversation_box = self.query_one("#conversation_box")
        await conversation_box.remove_children()
        await conversation_box.mount(MessageBox("Conversation effacée.", "SYSTEME : "))

    async def on_button_pressed(self) -> None:
        await self.process_conversation()

    async def on_input_submitted(self) -> None:
        await self.process_conversation()

    @work(exclusive=True, thread=True)
    async def listen(self):
        for m in self.conversation.subscriber.listen():
            if m["type"] == "message":
                conversation_box = self.query_one("#conversation_box")
                self.call_from_thread(
                    self.add_message_to_ui,
                    m["data"].decode("utf-8")
                )

    def add_message_to_ui(self, text):
        conversation_box = self.query_one("#conversation_box")
        conversation_box.mount(
            MessageBox(text, "")
        )
        conversation_box.scroll_end(animate=True)

    async def process_conversation(self) -> None:
        """Process a single question/answer in conversation."""
        message_input = self.query_one("#message_input", Input)
        conversation_box = self.query_one("#conversation_box")
        button = self.query_one("#send_button")

        if message_input.value == "":
            return

        if message_input.value.startswith("/username "):
            new_name = message_input.value.replace("/username ", "").strip()
            if new_name:
                self.user_name = new_name
                await conversation_box.mount(MessageBox(f"Pseudo changé en : {self.user_name}", "SYSTÈME : "))
                conversation_box.scroll_end(animate=True)
            message_input.value = ""
            return

        if message_input.value.startswith("/channel "):
            new_channel = message_input.value.replace("/channel ", "").strip()
            if new_channel:
                changed = self.conversation.change_channel(new_channel)
                if changed:
                    await conversation_box.mount(
                        MessageBox(f"Vous avez rejoint le canal : {new_channel}", "SYSTÈME : ")
                    )
                else:
                    await conversation_box.mount(
                        MessageBox(f"Vous êtes déjà sur le canal : {new_channel}", "SYSTÈME : ")
                    )
                conversation_box.scroll_end(animate=True)

            message_input.value = ""
            return

        self.toggle_widgets(message_input, button)

        with message_input.prevent(Input.Changed):
            full_message = f"[{self.conversation.channel}] {self.user_name} : {message_input.value}"
            await self.conversation.send(full_message)
            message_input.value = ""

        self.toggle_widgets(message_input, button)

    def toggle_widgets(self, *widgets: Widget) -> None:
        """Toggle a list of widgets."""
        for w in widgets:
            w.disabled = not w.disabled


if __name__ == "__main__":
    app = ChatApp()
    app.run()