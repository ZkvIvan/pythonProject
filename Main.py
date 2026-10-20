import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "code"))

import pyglet

pyglet.options['audio'] = ('pulse', 'openal', 'directsound', 'silent')

import arcade
from MainMenu import MainMenu
from Settings import settings
from utils import StartWindow, get_monitor_info, load_fonts


def main():
    load_fonts()

    mon_w, mon_h, _ = get_monitor_info()
    width = min(settings.get("resolution_width"), mon_w)
    height = min(settings.get("resolution_height"), mon_h)

    window = StartWindow(
        width=width,
        height=height,
        fullscreen=settings.get("fullscreen"),
        vsync=settings.get("vsync"),
        title="NightFall",
    )

    window.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()