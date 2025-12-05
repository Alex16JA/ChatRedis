from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.widget import Widget
from textual.widgets import Button, Footer, Header, Input, Static
from textual.message import Message
from textual import work
import redis
import requests


class StatusBar(Static):
    def __init__(self, host: str, channel: str, *args, **kwargs):
        text = f"{channel} ({host})"
        super().__init__(text, *args, **kwargs)

    def update_status(self, host: str, channel: str) -> None:
        self.update(f"{channel} ({host})")

class Conversation(Widget):

    def __init__(self):
        super().__init__()
        self.messages = []
        self.host = "localhost"
        self.redis_client = redis.StrictRedis(host=self.host, port=6379, db=0)
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

    def change_server(self, new_host):
        if new_host == self.host:
            return False

        try:
            self.subscriber.unsubscribe()
            self.redis_client.close()
        except:
            pass

        self.host = new_host
        self.redis_client = redis.StrictRedis(host=self.host, port=6379, db=0)
        self.subscriber = self.redis_client.pubsub()
        self.subscriber.subscribe(self.channel)
        return True

    def compose(self):
        yield Static("Test")

    async def send(self, message):
        try:
            self.redis_client.publish(self.channel, message)
        except:
            pass
        return message


class FocusableContainer(Container, can_focus=True):
    """Focusable container widget."""


class MessageBox(Widget, can_focus=True):
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
        yield StatusBar(
            self.conversation.host,
            self.conversation.channel,
            id="status_bar",
        )
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
                await conversation_box.mount(
                    MessageBox(
                        m["data"].decode("utf-8"),
                        "",
                    )
                )
                conversation_box.scroll_end(animate=True)

    async def process_conversation(self) -> None:
        message_input = self.query_one("#message_input", Input)
        conversation_box = self.query_one("#conversation_box")
        button = self.query_one("#send_button")
        status_bar = self.query_one(StatusBar)

        user_text = message_input.value.strip()
        if user_text == "":
            return

        message_input.value = ""

        if user_text.startswith("/"):
            parts = user_text.split(" ", 1)
            command = parts[0]
            arg = parts[1].strip() if len(parts) > 1 else ""

            match command:
                case "/username":
                    if arg:
                        self.user_name = arg
                        await conversation_box.mount(MessageBox(f"Pseudo changé en : {self.user_name}", "SYSTÈME : "))

                case "/channel":
                    if arg:
                        changed = self.conversation.change_channel(arg)
                        status = "Vous avez rejoint" if changed else "Vous êtes déjà sur"
                        await conversation_box.mount(MessageBox(f"{status} le canal : {arg}", "SYSTÈME : "))
                        status_bar.update_status(self.conversation.host, self.conversation.channel)

                case "/server":
                    if arg:
                        changed = self.conversation.change_server(arg)
                        if changed:
                            await conversation_box.mount(
                                MessageBox(f"Changement de serveur vers : {arg}", "SYSTÈME : "))
                            status_bar.update_status(self.conversation.host, self.conversation.channel)
                            self.listen()
                        else:
                            await conversation_box.mount(MessageBox(f"Déjà connecté sur : {arg}", "SYSTÈME : "))

                case "/weather":
                    cached_weather = self.conversation.redis_client.get("weather_paris")

                    if cached_weather:
                        await conversation_box.mount(
                            MessageBox(f"{cached_weather.decode('utf-8')}", "BOT : ")
                        )
                    else:
                            url = "https://api.open-meteo.com/v1/forecast?latitude=48.83692&longitude=2.32612&daily=temperature_2m_mean"
                            response = requests.get(url)
                            if response.status_code == 200:
                                data = response.json()
                                temp = data["daily"]["temperature_2m_mean"][0]
                                date = data["daily"]["time"][0]

                                weather_msg = f"Prévisions {date} : {temp}°C"

                                self.conversation.redis_client.set("weather_paris", weather_msg, ex=3600)

                                await conversation_box.mount(
                                    MessageBox(f"{weather_msg} ", "MÉTÉO : ")
                                )

                case _:
                    await conversation_box.mount(MessageBox(f"Commande inconnue : {command}", "ERREUR : "))

            conversation_box.scroll_end(animate=True)
            return

        self.toggle_widgets(message_input, button)

        with message_input.prevent(Input.Changed):
            full_message = f"[{self.conversation.channel}] {self.user_name} : {user_text}"
            await self.conversation.send(full_message)

        self.toggle_widgets(message_input, button)

    def toggle_widgets(self, *widgets: Widget) -> None:
        for w in widgets:
            w.disabled = not w.disabled


if __name__ == "__main__":
    app = ChatApp()
    app.run()