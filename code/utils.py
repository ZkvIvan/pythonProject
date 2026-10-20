import os
import arcade
import pyglet
import pyglet.display

from Settings import settings
from paths import asset


FONT_TITLE = "Vyaz Pixel"
FONT_UI = "Cyrillic Pixel-7"
BG_FRAME_DURATION = 1.0

def _load_font(file_names):
    for folder in ("fonts", ""):
        for name in file_names:
            path = asset(folder, name)
            if os.path.exists(path):
                arcade.load_font(path)
                return True
    print(f"[font] не найден ни один из файлов: {file_names}")
    return False


def load_fonts():
    _load_font(["Vyaz Pixel.ttf", "Vyaz_Pixel.ttf"])
    _load_font(["cyrillic_pixel-7.ttf", "Cyrillic Pixel-7.ttf"])


def get_monitor_info():
    try:
        width, height = arcade.get_display_size()
    except Exception as e:
        print(f"[monitor] не удалось узнать размер дисплея: {e}")
        width, height = 1920, 1080

    refresh_rate = 60
    try:
        screen = pyglet.display.get_display().get_default_screen()
        rate = screen.get_mode().rate
        if rate and rate > 0:
            refresh_rate = int(rate)
    except Exception as e:
        print(f"[monitor] fallback 60Hz: {e}")
    return width, height, refresh_rate


def apply_video_settings(window):
    try:
        mon_w, mon_h, _ = get_monitor_info()
        window.set_vsync(bool(settings.get("vsync")))

        if settings.get("fullscreen"):
            if not window.fullscreen:
                window.set_fullscreen(True)
            window.set_exclusive_mouse(True)
        else:
            if window.fullscreen:
                window.set_fullscreen(False)
            window.set_exclusive_mouse(False)
            w = min(int(settings.get("resolution_width")), mon_w)
            h = min(int(settings.get("resolution_height")), mon_h)
            window.set_size(w, h)
            window.center_window()
    except Exception as e:
        print(f"[video] не удалось применить настройки: {e}")


_BG_FRAMES = None


def load_bg_frames():
    global _BG_FRAMES
    if _BG_FRAMES is None:
        try:
            _BG_FRAMES = [
                arcade.load_texture(asset("images", "MainMenu", f"{n}.png"))
                for n in range(1, 11)
            ]
        except Exception as e:
            print(f"[bg] не удалось загрузить фон: {e}")
            _BG_FRAMES = []
    return _BG_FRAMES

class StartWindow(arcade.Window):
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720

    def __init__(self, width, height,
                 update_rate=1 / 60,
                 title="NightFall",
                 fullscreen=False,
                 resizable=True,
                 antialiasing=True,
                 vsync=True):
        super().__init__(
            width=width, height=height, title=title,
            fullscreen=fullscreen, resizable=resizable,
            update_rate=update_rate, antialiasing=antialiasing,
            vsync=vsync,
        )
        mon_w, mon_h, _ = get_monitor_info()
        self.set_minimum_size(min(self.MIN_WIDTH, mon_w),
                              min(self.MIN_HEIGHT, mon_h))
        if not fullscreen:
            self.center_window()