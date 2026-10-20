import arcade
import arcade.gui
import pyglet

from Settings import settings
from Audio import load_ui_sounds, start_menu_music
from ui_widgets import AnimatedBackground
from utils import load_bg_frames


class MenuView(arcade.View):

    def __init__(self):
        super().__init__()
        self.time = 0.0
        self.manager = arcade.gui.UIManager()
        self._active = False
        self._rebuild_pending = False

        self.background_list = arcade.SpriteList()
        self.animated_bg = None
        frames = load_bg_frames()
        if frames:
            self.animated_bg = AnimatedBackground(frames)
            self.background_list.append(self.animated_bg)

        self.hover_sound, self.click_sound = load_ui_sounds()

    def ui_scale(self):
        """1.0 при 720p, 2.0 при 1440p."""
        return max(1.0, min(2.0, self.window.height / 720))

    def request_rebuild(self):
        if self._rebuild_pending:
            return
        self._rebuild_pending = True
        pyglet.clock.schedule_once(self._do_rebuild, 0)

    def _do_rebuild(self, _dt):
        self._rebuild_pending = False
        if self._active:
            self._build_ui()

    def _build_ui(self):
        """Переопределяется наследниками."""
        raise NotImplementedError

    def _layout(self):
        if self.animated_bg is None:
            return
        w, h = self.window.width, self.window.height
        tex = self.animated_bg.texture
        self.animated_bg.scale = max(w / tex.width, h / tex.height)
        self.animated_bg.center_x = w / 2
        self.animated_bg.center_y = h / 2

    def on_show_view(self):
        self._active = True
        arcade.set_background_color(arcade.color.BLACK)
        try:
            self.window.set_exclusive_mouse(False)
        except Exception:
            pass
        self.manager.enable()
        self._layout()
        self._build_ui()
        start_menu_music()

    def on_hide_view(self):
        self._active = False
        self.manager.disable()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._layout()
        self.request_rebuild()

    def on_update(self, delta_time):
        self.time += delta_time
        if self.animated_bg is not None:
            speed = max(0.1, settings.get("animation_speed"))
            self.animated_bg.update_animation(delta_time * speed)

    def draw_background(self):
        self.clear()
        self.background_list.draw(pixelated=True)