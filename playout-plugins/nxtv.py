import json

from pydantic import BaseModel, Field

from nebula.plugins.playout import PlayoutPlugin, PlayoutPluginSlot


def jdata(**data):
    data = json.dumps(data).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{data}"'


class Context(BaseModel):
    showLogo: bool = Field(default=True, title="Show Logo")
    showClock: bool = Field(default=False, title="Show Clock")
    showInfo: bool = Field(default=False, title="Show Info")
    info: list[str] | None = Field(default=None, title="Info")


class Plugin(PlayoutPlugin):
    name = "nxtv"
    id_layer = 99
    slots = [
        PlayoutPluginSlot(type="action", name="Reboot"),
    ]

    def on_init(self):
        """Initialize the plugins

        this is executed when the playout controller
        starts. Create a context object to store the
        desired state of the HTML layer.
        """
        self.context = Context()
        self.boot()

    def boot(self):
        """Initialize the HTML layer"""
        self.query(f"CG {self.layer()} ADD 0 nxtv 1")
        self.flush()

    def flush(self):
        """Build the payload and send it to the playout server"""
        payload = jdata(**self.context.dict())
        self.query(f"CG {self.layer()} UPDATE 0 {payload}")

    def on_change(self):
        """Handle the change of the current item

        Based on the current clip, we decide what to show
        and what to hide and save the tasks to be executed.

        Keep in mind that the tasks are executed in order
        and cannot be skipped unless they return True.

        If the context has changed, we flush the changes,
        that will send the new state to the playout server.
        """
        ctx_changed = False

        self.tasks = []

        # do not show log on:
        # - folder 7 (jingles)
        # - folder 9 (ads)
        # - folder 10 (teleshopping)

        should_show_logo = self.current_item["id_folder"] not in [7, 9, 10]
        should_show_clock = self.current_item["id_folder"] not in [7, 9, 10]

        if should_show_logo != self.context.showLogo:
            self.context.showLogo = should_show_logo
            ctx_changed = True

        if should_show_clock != self.context.showClock:
            self.context.showClock = should_show_clock
            ctx_changed = True

        if self.current_item["id_folder"] in [1, 2, 3, 4, 5]:
            self.tasks.extend([self.show_now_playing, self.hide_now_playing])

        if ctx_changed:
            self.flush()

    def show_now_playing(self) -> bool:
        """Task to show now playing info

        Return false before clip reaches 5 seconds
        Then show the now playing information and 
        return True - that marks the task as done
        and will not be called again.
        """
        if self.position < 5:
            return False
        self.context.showInfo = True
        self.context.info = ["Now Playing:", self.current_item["title"]]
        self.flush()
        return True

    def hide_now_playing(self) -> bool:
        """Task to hide now playing info

        Return false before clip reaches 10 seconds
        Then hide the now playing information and
        return True - that marks the task as done
        and will not be called again
        """
        if self.position < 10:
            return False
        self.context.showInfo = False
        self.flush()
        return True

    def on_command(self, action, data) -> bool:
        """Interact with the plugin from the Firefly UI"""

        _ = action, data
        if action == "Reboot":
            self.boot()
            return True
        return False
