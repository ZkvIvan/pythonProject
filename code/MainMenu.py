# ============================================================
# MainMenu.py — главное меню.
# ============================================================

import math
import arcade
import arcade.gui
from arcade import gl

from Audio import stop_menu_music
from ui_widgets import SoundButton, make_style, CLEAR
from menu_base import MenuView
from utils import FONT_TITLE
from GameView import GameView


class MainMenu(MenuView):
    def __init__(self):
        super().__init__()

        self.title_shadow = arcade.Text(
            text="NightFall", x=0, y=0,
            color=arcade.color.BLACK,
            font_size=64, font_name=FONT_TITLE,
            anchor_x="left", anchor_y="top",
        )
        self.title_text = arcade.Text(
            text="NightFall", x=0, y=0,
            color=arcade.color.WHITE,
            font_size=64, font_name=FONT_TITLE,
            anchor_x="left", anchor_y="top",
        )

    # ---------------- Действия кнопок ----------------

    def _start_game(self, _event):
        stop_menu_music()
        self.window.show_view(GameView())

    def _open_settings(self, _event):
        from SettingMenu import SettingMenu
        self.window.show_view(SettingMenu())

    def _open_education(self, _event):
        from Education import EducationView
        self.window.show_view(EducationView())

    def _exit(self, _event):
        arcade.exit()

    # ---------------- UI ----------------

    def _build_ui(self):
        s = self.ui_scale()
        w = self.window.width

        gap = int(30 * s)
        btn_w = int(min(280 * s, (w * 0.94 - 3 * gap) / 4))
        btn_h = int(100 * s)
        style = make_style(int(28 * s), CLEAR, 0)

        items = [
            ("Начать игру", self._start_game),
            ("Настройки", self._open_settings),
            ("Обучение", self._open_education),
            ("Выход", self._exit),
        ]

        h_box = arcade.gui.UIBoxLayout(vertical=False, space_between=gap)
        for text, callback in items:
            h_box.add(SoundButton(
                text=text, width=btn_w, height=btn_h, style=style,
                hover_sound=self.hover_sound, click_sound=self.click_sound,
                callback=callback,
            ))

        self.manager.clear()
        anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        anchor.add(
            child=h_box,
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=int(80 * s),
        )

    def _layout(self):
        super()._layout()
        w, h = self.window.width, self.window.height
        font_size = max(24, int(h * 0.1))
        margin_x = int(w * 0.03)
        margin_y = int(h * 0.05)

        self.title_text.font_size = font_size
        self.title_text.x = margin_x
        self.title_text.y = h - margin_y

        self.title_shadow.font_size = font_size
        self.title_shadow.x = margin_x + 4
        self.title_shadow.y = h - margin_y - 4

    def on_draw(self):
        self.draw_background()

        alpha = 200 + int(math.sin(self.time * 2) * 55)
        self.title_text.color = (255, 255, 255, alpha)
        self.title_shadow.draw()
        self.title_text.draw()

        self.manager.draw(filter=gl.NEAREST)
