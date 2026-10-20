import arcade
import arcade.gui
import math

from utils import FONT_TITLE, FONT_UI
from Audio import play_game_sound


class TutorialIntro(arcade.View):
    def __init__(self, profile):
        super().__init__()
        self.profile = profile
        self.time = 0.0
        self.manager = arcade.gui.UIManager()
        self.lore = (
            "Ты очнулся в чужом теле. Стол перед тобой покрыт пылью и кровью.\n"
            "Правила просты: выживи — или стань частью колоды.\n\n"
            "Первая ночь — лишь проба сил. Ткач даст тебе шанс понять правила,\n"
            "прежде чем швырнёт в настоящий кошмар."
        )
        self._lore_text = None
        self._lore_key = None

    def on_show_view(self):
        self.manager.enable()
        s = self.window.height / 1080
        btn = arcade.gui.UIFlatButton(
            text="НАЧАТЬ", width=int(240 * s), height=int(64 * s),
            style={
                "normal": arcade.gui.UIFlatButton.UIStyle(
                    font_name=FONT_TITLE, font_size=int(22 * s),
                    font_color=arcade.color.WHITE,
                    bg=(40, 10, 10, 255),
                    border=(200, 40, 40, 255), border_width=2),
                "hover": arcade.gui.UIFlatButton.UIStyle(
                    font_name=FONT_TITLE, font_size=int(22 * s),
                    font_color=arcade.color.WHITE,
                    bg=(70, 20, 20, 255),
                    border=(255, 90, 90, 255), border_width=3),
                "press": arcade.gui.UIFlatButton.UIStyle(
                    font_name=FONT_TITLE, font_size=int(22 * s),
                    font_color=arcade.color.WHITE,
                    bg=(90, 25, 25, 255),
                    border=(255, 90, 90, 255), border_width=3),
            }
        )

        @btn.event("on_click")
        def _go(event):
            play_game_sound("ui_click")
            from GameView import GameView
            self.window.show_view(GameView(profile=self.profile, night=1))

        anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        anchor.add(child=btn, anchor_x="center_x", anchor_y="bottom",
                   align_y=int(80 * s))

    def on_hide_view(self):
        self.manager.disable()

    def on_update(self, dt):
        self.time += dt

    def _build_lore_text(self, w, h, s):
        top_limit = h - 300 * s
        bot_limit = 200 * s
        available_h = top_limit - bot_limit
        max_w = int(min(w * 0.82, 1000 * s))

        font_size = int(22 * s)
        txt = None
        while font_size >= 11:
            txt = arcade.Text(
                self.lore, 0, 0,
                (200, 200, 200), font_size,
                font_name=FONT_UI,
                width=max_w, multiline=True, align="center",
            )
            if txt.content_height <= available_h:
                break
            font_size -= 1

        if txt is None:
            return None

        center_y = (top_limit + bot_limit) / 2
        txt.x = w / 2
        txt.y = center_y + txt.content_height / 2
        txt.anchor_x = "center"
        txt.anchor_y = "top"
        return txt

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        s = h / 1080

        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (6, 4, 6))
        pulse = 0.6 + 0.4 * math.sin(self.time * 1.5)
        arcade.draw_circle_filled(w / 2, h / 2, 500 * s,
                                  (40, 4, 4, int(100 * pulse)))

        arcade.draw_text("НОЧЬ 1", w / 2, h - 180 * s, (200, 30, 30),
                         54 * s, font_name=FONT_TITLE, anchor_x="center")
        arcade.draw_text("ОБУЧЕНИЕ", w / 2, h - 250 * s, (255, 200, 80),
                         32 * s, font_name=FONT_TITLE, anchor_x="center")

        key = (int(w), int(h))
        if self._lore_key != key or self._lore_text is None:
            self._lore_text = self._build_lore_text(w, h, s)
            self._lore_key = key
        if self._lore_text is not None:
            self._lore_text.draw()

        arcade.draw_text(f"Герой: {self.profile.player_name}",
                         w / 2, 150 * s, (150, 150, 160),
                         18 * s, font_name=FONT_UI, anchor_x="center")

        self.manager.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ENTER:
            from GameView import GameView
            self.window.show_view(GameView(profile=self.profile, night=1))