import arcade
import json
import math

from paths import data
from utils import FONT_TITLE, FONT_UI
from profile import Profile, starter_utils
from Audio import play_game_sound


CARD_W = 240
CARD_H = 360

_CONFIRM_KEYS = tuple(
    v for v in (
        getattr(arcade.key, "ENTER", None),
        getattr(arcade.key, "RETURN", None),
        getattr(arcade.key, "NUM_ENTER", None),
    ) if v is not None
)


class CharacterSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        self.name_text = "Жнец"
        self.max_name_len = 16
        self.input_focused = False

        try:
            with open(data("characters.json"), "r", encoding="utf-8") as f:
                self.heroes = json.load(f)
        except Exception as e:
            print(f"[select] characters: {e}")
            self.heroes = []
        try:
            with open(data("cards.json"), "r", encoding="utf-8") as f:
                self.cards_by_id = {c["id"]: c for c in json.load(f)}
        except Exception:
            self.cards_by_id = {}

        self.hover_hero = 0 if self.heroes else None
        self.time = 0.0
        self._btn_start = (0, 0, 0, 0)
        self._btn_back = (0, 0, 0, 0)
        self._input_rect = (0, 0, 0, 0)

    def on_show_view(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        print(f"[CharacterSelectView] loaded | win={w}x{h} s={s:.3f}")
        print(f"[CharacterSelectView] heroes={len(self.heroes)} "
              f"cards={len(self.cards_by_id)}")

    def _start_game(self):
        play_game_sound("ui_click")
        if not self.heroes:
            print("[select] нет персонажей в characters.json")
            return
        idx = self.hover_hero if self.hover_hero is not None else 0
        hero = self.heroes[idx]
        p_name = self.name_text.strip() or "Жнец"
        try:
            utils = starter_utils(3)
            profile = Profile.new_game(hero["id"], p_name,
                                        hero.get("deck", []), utils)
            profile.save()
        except Exception as e:
            import traceback
            print(f"[select] profile error: {e}")
            traceback.print_exc()
            return

        try:
            from TutorialIntro import TutorialIntro
            self.window.show_view(TutorialIntro(profile))
        except Exception:
            try:
                from GameView import GameView
                self.window.show_view(GameView(profile=profile, night=1))
            except Exception:
                import traceback
                traceback.print_exc()

    def _go_back(self):
        from MainMenu import MainMenu
        self.window.show_view(MainMenu())

    def _layout(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        n = len(self.heroes)

        cw = int(CARD_W * s)
        ch = int(CARD_H * s)
        gap = int(30 * s)
        total_w = n * cw + max(0, n - 1) * gap
        start_x = (w - total_w) / 2
        card_y = h / 2 - ch / 2 + int(30 * s)

        iw = int(360 * s)
        ih = int(58 * s)
        ix = w / 2 - iw / 2
        iy = h - int(305 * s)

        return {
            "s": s, "w": w, "h": h,
            "cw": cw, "ch": ch, "gap": gap,
            "start_x": start_x, "card_y": card_y,
            "input_rect": (ix, iy, iw, ih),
        }

    def on_draw(self):
        self.clear()
        L = self._layout()
        s, w, h = L["s"], L["w"], L["h"]

        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (8, 8, 12))

        title_y = h - int(80 * s)
        arcade.draw_text("ВЫБЕРИТЕ СУДЬБУ", w / 2, title_y,
                         (60, 5, 5), 46 * s,
                         font_name=FONT_TITLE, anchor_x="center")
        arcade.draw_text("ВЫБЕРИТЕ СУДЬБУ", w / 2, title_y - 4 * s,
                         (220, 40, 40), 46 * s,
                         font_name=FONT_TITLE, anchor_x="center")

        arcade.draw_text("Каждый герой — свой путь. Своя колода. Свой финал.",
                         w / 2, title_y - int(78 * s),
                         (120, 120, 130), 15 * s,
                         font_name=FONT_UI, anchor_x="center")

        arcade.draw_text("Введите имя героя:",
                         w / 2, h - int(250 * s),
                         (220, 220, 230), 18 * s,
                         font_name=FONT_UI, anchor_x="center")

        ix, iy, iw, ih = L["input_rect"]
        self._input_rect = (ix, iy, iw, ih)

        pulse = 0.5 + 0.5 * math.sin(self.time * 3)

        glow_a = 90 if self.input_focused else int(35 + 35 * pulse)
        arcade.draw_lbwh_rectangle_filled(ix - 8, iy - 8, iw + 16, ih + 16,
                                          (200, 40, 40, glow_a))

        arcade.draw_lbwh_rectangle_filled(ix, iy, iw, ih, (18, 18, 24))

        border_a = 255 if self.input_focused else int(180 + 75 * pulse)
        arcade.draw_lbwh_rectangle_outline(ix, iy, iw, ih,
                                           (255, 90, 90, border_a), 3)

        blink = (math.sin(self.time * 5) + 1) / 2
        if self.input_focused:
            cursor = "|" if blink > 0.5 else " "
        else:
            cursor = ""
        if self.name_text:
            display = self.name_text + cursor
            color = (255, 245, 245)
        else:
            display = "нажми сюда, чтобы ввести имя" + cursor
            color = (140, 140, 150)
        arcade.draw_text(display,
                         ix + iw / 2, iy + ih / 2,
                         color, 22 * s,
                         font_name=FONT_UI,
                         anchor_x="center", anchor_y="center")

        arcade.draw_text(f"{len(self.name_text)}/{self.max_name_len}",
                         ix + iw - 8 * s, iy + 6 * s,
                         (120, 120, 130), 12 * s,
                         font_name=FONT_UI,
                         anchor_x="right", anchor_y="bottom")

        for i, hero in enumerate(self.heroes):
            cx = L["start_x"] + i * (L["cw"] + L["gap"])
            self._draw_hero_card(hero, cx, L["card_y"],
                                 L["cw"], L["ch"], i == self.hover_hero, s)

        self._draw_buttons(w, s)

        arcade.draw_text("[ENTER] — начать      [ESC] — назад",
                         w / 2, int(40 * s), (140, 140, 150), 14 * s,
                         font_name=FONT_UI, anchor_x="center")

    def _draw_buttons(self, w, s):
        bw = int(220 * s)
        bh = int(56 * s)
        bx = w / 2 - bw / 2
        by = int(85 * s)
        arcade.draw_lbwh_rectangle_filled(bx, by, bw, bh, (40, 10, 10))
        arcade.draw_lbwh_rectangle_outline(bx, by, bw, bh, (220, 40, 40), 2)
        arcade.draw_text("НАЧАТЬ ПУТЬ",
                         bx + bw / 2, by + bh / 2, arcade.color.WHITE,
                         20 * s, font_name=FONT_TITLE,
                         anchor_x="center", anchor_y="center")
        self._btn_start = (bx, by, bw, bh)

        bw2 = int(150 * s)
        bx2 = int(40 * s)
        by2 = int(30 * s)
        arcade.draw_lbwh_rectangle_filled(bx2, by2, bw2, bh, (15, 15, 20))
        arcade.draw_lbwh_rectangle_outline(bx2, by2, bw2, bh,
                                           (100, 100, 100), 1)
        arcade.draw_text("НАЗАД",
                         bx2 + bw2 / 2, by2 + bh / 2, (180, 180, 180),
                         18 * s, font_name=FONT_UI,
                         anchor_x="center", anchor_y="center")
        self._btn_back = (bx2, by2, bw2, bh)

    def _draw_hero_card(self, hero, x, y, cw, ch, hovered, s):
        bg = (30, 12, 12) if hovered else (18, 18, 22)
        border = (200, 40, 40) if hovered else (70, 70, 80)
        border_w = 3 if hovered else 2

        arcade.draw_lbwh_rectangle_filled(x, y, cw, ch, bg)
        arcade.draw_lbwh_rectangle_outline(x, y, cw, ch, border, border_w)

        accent = (180, 30, 30) if hovered else (60, 60, 70)
        arcade.draw_lbwh_rectangle_filled(x, y + ch - int(6 * s),
                                          cw, int(6 * s), accent)

        pad = int(16 * s)
        inner_w = cw - pad * 2

        name_y = y + ch - int(50 * s)
        arcade.draw_text(hero.get("name", "?"), x + cw / 2, name_y,
                         arcade.color.WHITE if hovered else (200, 200, 210),
                         24 * s, font_name=FONT_TITLE,
                         anchor_x="center", anchor_y="center",
                         width=int(inner_w), align="center")

        arcade.draw_text(f"♥ HP: {hero.get('hp', 100)}",
                         x + pad, name_y - int(40 * s),
                         (220, 100, 100), 14 * s, font_name=FONT_UI)
        arcade.draw_text(f"♦ Колода: {len(hero.get('deck', []))}",
                         x + cw - pad, name_y - int(40 * s),
                         (200, 180, 100), 14 * s, font_name=FONT_UI,
                         anchor_x="right")

        arcade.draw_lbwh_rectangle_filled(x + pad, name_y - int(55 * s),
                                          inner_w, 1, (80, 80, 90))

        ab_y = name_y - int(70 * s)
        arcade.draw_text("СПОСОБНОСТЬ", x + pad, ab_y,
                         (255, 180, 60), 12 * s, font_name=FONT_UI)
        arcade.draw_text(hero.get("ability_name", ""),
                         x + pad, ab_y - int(22 * s),
                         (255, 220, 120) if hovered else (220, 200, 140),
                         16 * s, font_name=FONT_UI, width=int(inner_w))
        arcade.draw_text(hero.get("ability_text", ""),
                         x + pad, ab_y - int(50 * s),
                         (180, 180, 190), 13 * s, font_name=FONT_UI,
                         width=int(inner_w), multiline=True)

        deck_y = y + int(90 * s)
        arcade.draw_text("СТАРТОВАЯ КОЛОДА", x + pad, deck_y + int(30 * s),
                         (150, 150, 160), 11 * s, font_name=FONT_UI)
        card_ids = hero.get("deck", [])[:6]
        if not card_ids:
            return
        mini_w = (inner_w - 5 * 4 * s) / 6
        mini_h = mini_w * 1.4
        for j, cid in enumerate(card_ids):
            info = self.cards_by_id.get(cid, {})
            mx = x + pad + j * (mini_w + 4 * s)
            my = deck_y - mini_h + int(20 * s)
            rarity = info.get("rarity", "common")
            rcol = {
                "common": (170, 170, 170),
                "rare": (90, 150, 255),
                "legendary": (255, 200, 50),
            }.get(rarity, (170, 170, 170))
            arcade.draw_lbwh_rectangle_filled(mx, my, mini_w, mini_h,
                                              (40, 30, 30))
            arcade.draw_lbwh_rectangle_outline(mx, my, mini_w, mini_h,
                                               rcol, 1)

    def on_update(self, dt):
        self.time += dt

    def on_mouse_motion(self, x, y, dx, dy):
        L = self._layout()
        self.hover_hero = None
        for i in range(len(self.heroes)):
            cx = L["start_x"] + i * (L["cw"] + L["gap"])
            if (cx <= x <= cx + L["cw"]
                    and L["card_y"] <= y <= L["card_y"] + L["ch"]):
                self.hover_hero = i
                break

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return

        bx, by, bw, bh = self._btn_start
        if bx <= x <= bx + bw and by <= y <= by + bh:
            self._start_game()
            return
        bx, by, bw, bh = self._btn_back
        if bx <= x <= bx + bw and by <= y <= by + bh:
            self._go_back()
            return

        ix, iy, iw, ih = self._input_rect
        if ix <= x <= ix + iw and iy <= y <= iy + ih:
            self.input_focused = True
            print(f"[CharacterSelectView] input focused | name='{self.name_text}'")
            return
        self.input_focused = False

        L = self._layout()
        for i in range(len(self.heroes)):
            cx = L["start_x"] + i * (L["cw"] + L["gap"])
            if (cx <= x <= cx + L["cw"]
                    and L["card_y"] <= y <= L["card_y"] + L["ch"]):
                self.hover_hero = i
                self._start_game()
                return

    def on_text(self, text):
        if not self.input_focused:
            return
        if not text:
            return
        cleaned = "".join(c for c in text if c.isprintable())
        if not cleaned:
            return
        room = self.max_name_len - len(self.name_text)
        if room <= 0:
            return
        self.name_text += cleaned[:room]

    def on_key_press(self, key, modifiers):
        if key == arcade.key.BACKSPACE:
            if self.input_focused:
                self.name_text = self.name_text[:-1]
            return
        if key in _CONFIRM_KEYS:
            self._start_game()
            return
        if key == arcade.key.ESCAPE:
            self._go_back()
            return