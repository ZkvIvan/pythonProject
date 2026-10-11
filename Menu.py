import arcade
import pyglet
import pyglet.display
import arcade.gui
from GameView import GameView


def get_monitor_info():
    width, height = arcade.get_display_size()
    refresh_rate = 30
    screen = pyglet.display.get_display().get_default_screen()
    rate = screen.get_mode().rate // 1000
    if rate and rate > 0:
        refresh_rate = rate
    return width, height, refresh_rate

width, height, hz = get_monitor_info()

class AnimatedBackground(arcade.Sprite):
    def __init__(self, textures, frame_duration=0.8, scale=1.0):
        super().__init__(textures[0], scale=scale)
        self.textures = textures
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.timer = 0.0

    def update_animation(self, delta_time=1/hz):
        self.timer += delta_time
        if self.timer >= self.frame_duration:
            self.timer = 0.0
            self.current_frame = (self.current_frame + 1) % len(self.textures)
            self.texture = self.textures[self.current_frame]


class SoundButton(arcade.gui.UIFlatButton):
    def __init__(self, *args, hover_sound=None, click_sound=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self._hover_played = False

    def on_hover(self):
        super().on_hover()
        if not self._hover_played and self.hover_sound:
            self._hover_player = arcade.play_sound(self.hover_sound)
            self._hover_played = True

    def on_leave(self):
        super().on_leave()
        self._hover_played = False  

    def on_click(self, event):
        super().on_click(event)
        if self.click_sound:
            self._click_player = arcade.play_sound(self.click_sound)

class StartWindow(arcade.Window):
    def __init__(self, width, height, update_rate=1/60,
                title="build_1", fullscreen=True,
                 resizable=True, antialiasing=True, vsync=True):
        super().__init__(
            width=width,
            height=height,
            title=title,
            fullscreen=fullscreen,
            resizable=resizable,
            update_rate=update_rate,
            antialiasing=antialiasing,
            vsync=vsync,
        )


class MainMenu(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.background_list = arcade.SpriteList()
        self.animated_bg = None

        self.hover_sound = arcade.load_sound("sounds/hover.wav")
        self.click_sound = arcade.load_sound("sounds/click.wav")
        self.hover_sound = None
        self.click_sound = None

        transparent_style = {
            "normal": arcade.gui.UIFlatButton.UIStyle(
                font_color=arcade.color.WHITE,
                bg=(0, 0, 0, 0),
                border_width=0,
            ),
            "hover": arcade.gui.UIFlatButton.UIStyle(
                font_color=arcade.color.WHITE,
                bg=(0, 0, 0, 0),
                border_width=2,
                border=arcade.color.WHITE,
            ),
            "press": arcade.gui.UIFlatButton.UIStyle(
                font_color=arcade.color.LIGHT_GRAY,
                bg=(0, 0, 0, 0),
                border_width=2,
                border=arcade.color.LIGHT_GRAY,
            ),
        }

        start_button = SoundButton(
            text="Начать игру", width=200, height=50,
            style=transparent_style,
            hover_sound=self.hover_sound, click_sound=self.click_sound,
        )
        settings_button = SoundButton(
            text="Настройки", width=200, height=50,
            style=transparent_style,
            hover_sound=self.hover_sound, click_sound=self.click_sound,
        )
        education_button = SoundButton(
            text="Обучение", width=200, height=50,
            style=transparent_style,
            hover_sound=self.hover_sound, click_sound=self.click_sound,
        )
        exit_button = SoundButton(
            text="Выход", width=200, height=50,
            style=transparent_style,
            hover_sound=self.hover_sound, click_sound=self.click_sound,
        )

        @start_button.event("on_click")
        def on_click_start(event):
            self.window.show_view(GameView())

        @settings_button.event("on_click")
        def on_click_settings(event):
            self.window.show_view(SettingMenu())

        @education_button.event("on_click")
        def on_click_education(event):
            print("Обучение — TODO")

        @exit_button.event("on_click")
        def on_click_exit(event):
            arcade.exit()

        v_box = arcade.gui.UIBoxLayout(space_between=15)
        v_box.add(start_button)
        v_box.add(settings_button)
        v_box.add(education_button)
        v_box.add(exit_button)

        anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        anchor.add(anchor_x="left", anchor_y="center_y", child=v_box)

    def on_show_view(self):
        self.manager.enable()
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

        frames = []
        for number in range(1, 13):
            texture = arcade.load_texture(f'images/MainMenu/{number}.png')
            frames.append(texture)

        self.animated_bg = AnimatedBackground(frames, frame_duration=0.5, scale=1.0)
        self.animated_bg.center_x = self.window.width / 2
        self.animated_bg.center_y = self.window.height / 2

        scale_x = self.window.width / self.animated_bg.texture.width
        scale_y = self.window.height / self.animated_bg.texture.height
        self.animated_bg.scale = max(scale_x, scale_y)

        self.background_list.append(self.animated_bg)

    def on_hide_view(self):
        self.manager.disable()

    def on_update(self, delta_time):
        if self.animated_bg is not None:
            self.animated_bg.update_animation(delta_time)

    def on_draw(self):
        self.clear()
        self.background_list.draw()
        self.manager.draw()


class SettingMenu(arcade.View):
    pass