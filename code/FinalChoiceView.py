import arcade
from utils import FONT_TITLE, FONT_UI
from profile import Profile, starter_utils
import json
from paths import data

class FinalChoiceView(arcade.View):
    def __init__(self, player_name, cards_collected):
        super().__init__()
        self.player_name = player_name
        self.cards_collected = cards_collected
        self.hover_left = False
        self.hover_right = False
        self.lore_text = (
            "Ты дошел до дна. За столом больше нет Ткача. Осталась лишь его тень,\n"
            "и пустой трон из костей. Ты побеждал, но ты лишь исполнял его волю.\n"
            "Он устал быть Богом этого гниющего мира и ушел в Пустоту.\n\n"
            "Теперь ты стоишь перед выбором, Жнец."
        )

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        s = h / 1080
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (3, 2, 2))
        arcade.draw_circle_filled(w / 2, h / 2, 400 * s, (12, 4, 4, 120))
        arcade.draw_text(f"КОНЕЦ ПУТИ, {self.player_name}",
                         w / 2, h - 120 * s, (90, 10, 10), 36 * s,
                         font_name=FONT_TITLE, anchor_x="center")
        arcade.draw_text(self.lore_text, w / 2, h / 2 + 150 * s,
                         (140, 130, 130), 20 * s, font_name=FONT_UI,
                         anchor_x="center", align="center", width=int(900 * s))

        left = arcade.LBWH(w / 2 - 450 * s, h / 2 - 250 * s,
                           400 * s, 160 * s)
        c_left = (30, 5, 5) if self.hover_left else (10, 2, 2)
        b_left = (120, 20, 20) if self.hover_left else (40, 10, 10)
        arcade.draw_lbwh_rectangle_filled(left.left, left.bottom,
                                          left.width, left.height, c_left)
        arcade.draw_lbwh_rectangle_outline(left.left, left.bottom,
                                           left.width, left.height, b_left, 3)
        arcade.draw_text("ПРИНЯТЬ ПУСТОТУ\n\n(Стать новым Ткачом)",
                         left.center_x, left.center_y,
                         (200, 150, 150), 20 * s, font_name=FONT_UI,
                         anchor_x="center", anchor_y="center", align="center")

        right = arcade.LBWH(w / 2 + 50 * s, h / 2 - 250 * s,
                            400 * s, 160 * s)
        c_right = (20, 20, 20) if self.hover_right else (8, 8, 8)
        b_right = (80, 80, 80) if self.hover_right else (30, 30, 30)
        arcade.draw_lbwh_rectangle_filled(right.left, right.bottom,
                                          right.width, right.height, c_right)
        arcade.draw_lbwh_rectangle_outline(right.left, right.bottom,
                                           right.width, right.height, b_right, 3)
        arcade.draw_text("РАЗОРВАТЬ ПЕТЛЮ\n\n(Позволить миру сгнить)",
                         right.center_x, right.center_y,
                         (150, 150, 150), 20 * s, font_name=FONT_UI,
                         anchor_x="center", anchor_y="center", align="center")

    def on_mouse_motion(self, x, y, dx, dy):
        w, h = self.window.width, self.window.height
        s = h / 1080
        self.hover_left = (w / 2 - 450 * s <= x <= w / 2 - 50 * s
                           and h / 2 - 250 * s <= y <= h / 2 - 90 * s)
        self.hover_right = (w / 2 + 50 * s <= x <= w / 2 + 450 * s
                            and h / 2 - 250 * s <= y <= h / 2 - 90 * s)

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
        w, h = self.window.width, self.window.height
        s = h / 1080
        if (w / 2 - 450 * s <= x <= w / 2 - 50 * s
                and h / 2 - 250 * s <= y <= h / 2 - 90 * s):
            # NG+ — создаём новый профиль
            try:
                with open(data("characters.json"), "r", encoding="utf-8") as f:
                    heroes = json.load(f)
                hero = heroes[0]
                deck = hero["deck"]
            except Exception:
                deck = []
            prof = Profile.new_game("knight", self.player_name, deck,
                                    starter_utils())
            prof.save()
            from TutorialIntro import TutorialIntro
            self.window.show_view(TutorialIntro(prof))
        elif (w / 2 + 50 * s <= x <= w / 2 + 450 * s
              and h / 2 - 250 * s <= y <= h / 2 - 90 * s):
            from EndGameView import EndGameView
            self.window.show_view(EndGameView(self.player_name,
                                              self.cards_collected))