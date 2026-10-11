import pyglet
pyglet.options['audio'] = ('pulse',)

import arcade
from Menu import MainMenu, StartWindow, get_monitor_info

def main():
    width, height, hz = get_monitor_info()
    window = StartWindow(width, height, vsync=True, fullscreen=False, title="build_1")
    window.show_view(MainMenu())
    arcade.run()


if __name__ == "__main__":
    main()
