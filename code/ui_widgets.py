# ============================================================
# ui_widgets.py — визуальные элементы интерфейса:
#   - AnimatedBackground (спрайт-анимация)
#   - make_style (сборка стиля кнопки)
#   - SoundButton (кнопка с hover/click звуками)
#   - ToggleButton (кнопка ВКЛ/ВЫКЛ)
# ============================================================

import arcade
import arcade.gui

from Audio import play_sfx
from Settings import settings
from utils import FONT_UI, BG_FRAME_DURATION


# Цвета стиля
GRAY = (90, 90, 90, 255)
CLEAR = (0, 0, 0, 0)


def make_style(font_size, normal_border=GRAY, normal_border_width=1,
               font_color=arcade.color.WHITE):
    """Стиль кнопки: прозрачный фон, рамка; hover/press — яркая рамка."""
    UIStyle = arcade.gui.UIFlatButton.UIStyle

    def state(color, border, border_width):
        return UIStyle(
            font_color=color,
            font_name=FONT_UI,
            font_size=font_size,
            bg=CLEAR,
            border=border,
            border_width=border_width,
        )

    return {
        "normal": state(font_color, normal_border, normal_border_width),
        "hover": state(arcade.color.WHITE, arcade.color.WHITE, 2),
        "press": state(arcade.color.LIGHT_GRAY, arcade.color.LIGHT_GRAY, 2),
    }


class AnimatedBackground(arcade.Sprite):
    """Спрайт с покадровой анимацией."""
    def __init__(self, textures, frame_duration=BG_FRAME_DURATION, scale=1.0):
        super().__init__(textures[0], scale=scale)
        self.frames = textures
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.timer = 0.0

    def update_animation(self, delta_time=1 / 60):
        self.timer += delta_time
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.texture = self.frames[self.current_frame]


class SoundButton(arcade.gui.UIFlatButton):
    """Кнопка с звуками наведения и клика."""
    def __init__(self, *args, hover_sound=None, click_sound=None,
                 callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self.callback = callback
        self._was_hovered = bool(self.hovered)

    def on_event(self, event):
        result = super().on_event(event)
        hovered = bool(self.hovered)
        if hovered and not self._was_hovered:
            play_sfx(self.hover_sound)
        self._was_hovered = hovered
        return result

    def on_click(self, event):
        super().on_click(event)
        play_sfx(self.click_sound)
        if self.callback:
            self.callback(event)


class ToggleButton(arcade.gui.UIFlatButton):
    """Кнопка-переключатель ВКЛ/ВЫКЛ, хранящая состояние в settings."""
    @staticmethod
    def _style_for(state, font_size):
        if state:
            return make_style(font_size, arcade.color.WHITE, 2,
                              arcade.color.WHITE)
        return make_style(font_size, GRAY, 1, (150, 150, 150, 255))

    def __init__(self, *, setting_key, on_change=None, font_size=20,
                 width=120, height=48):
        state = bool(settings.get(setting_key))
        super().__init__(
            text="ВКЛ" if state else "ВЫКЛ",
            width=width, height=height,
            style=ToggleButton._style_for(state, font_size),
        )
        self.setting_key = setting_key
        self._on_change_cb = on_change
        self._font_size = font_size

    def on_click(self, event):
        super().on_click(event)
        new_state = not settings.get(self.setting_key)
        settings.set(self.setting_key, new_state)
        self.text = "ВКЛ" if new_state else "ВЫКЛ"
        self.style = ToggleButton._style_for(new_state, self._font_size)
        self.trigger_render()
        if self._on_change_cb:
            self._on_change_cb(new_state)