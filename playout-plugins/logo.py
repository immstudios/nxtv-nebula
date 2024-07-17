"""
This is not the actual logo plugin used with NXTV, 
but it is the simplest example of logo plugin implementation

It assumes a "logo.png" file is present in the media folder.
The image has to be in the same resolution as the playout
channel (1920x1080) and the logo has to be positioned in the
desired location.

When playout plays a clip from the folder 7 (which is the
default for jingles), the logo will be hidden. Otherwise,
the logo will be shown.
"""

from nebula.plugins.playout import PlayoutPlugin


class Plugin(PlayoutPlugin):
    name = "logo"
    id_layer = 100

    def on_init(self):
        self.query(f"PLAY {self.layer()} logo")

    def on_change(self):
        if self.current_item["id_folder"] == 7:
            self.query(f"PLAY {self.layer()} empty")
        else:
            self.query(f"PLAY {self.layer()} logo")

    def on_command(self, action, data):
        _ = data
        if action == "hide":
            self.query(f"PLAY {self.layer()} empty")
        elif action == "show":
            self.query(f"PLAY {self.layer()} logo")

        return True
