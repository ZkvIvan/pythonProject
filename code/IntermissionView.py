import arcade, json, math, random
from paths import data
from utils import FONT_TITLE, FONT_UI
from Audio import play_game_sound

_CONFIRM_KEYS = tuple(v for n in ("ENTER", "RETURN", "NUM_ENTER") if (v := getattr(arcade.key, n, None)) is not None)
RARITY_PRICE = {"common": 30, "rare": 60, "legendary": 120}
RARITY_COLOR = {"common": (170, 170, 170), "rare": (90, 150, 255), "legendary": (255, 200, 50)}
CARD_W, CARD_H, UTIL_W, UTIL_H = 110, 154, 120, 100

def _clamp255(v): return max(0, min(255, int(v)))

class IntermissionView(arcade.View):
    def __init__(self, profile, next_night):
        super().__init__()
        self.profile, self.next_night, self.tab, self.time = profile, next_night, "deck", 0.0
        self.cards_by_id, self.utils_by_id = {}, {}
        try:
            with open(data("cards.json"), "r", encoding="utf-8") as f:
                for c in json.load(f): self.cards_by_id[c["id"]] = c
            with open(data("utilities.json"), "r", encoding="utf-8") as f:
                for u in json.load(f): self.utils_by_id[u["id"]] = u
        except Exception as e: print(f"[intermission] data: {e}")
        self.shop_items, self._reroll_shop()
        self._btn_rects, self.message, self.message_age = [], "", 10.0
        self.last_rewards = getattr(profile, "last_rewards", None)

    def on_show_view(self): print(f"[IntermissionView] ночь {self.next_night} — загружен")

    def _reroll_shop(self):
        pool = [cid for cid in self.cards_by_id if cid not in self.profile.owned_cards]; random.shuffle(pool)
        self.shop_items = []
        for cid in pool[:4]:
            info = self.cards_by_id[cid]; price = RARITY_PRICE.get(info.get("rarity", "common"), 30) + random.randint(-10, 20)
            self.shop_items.append({"id": cid, "price": max(10, price)})

    def _flash(self, msg): self.message, self.message_age = msg, 0.0
    def _card_name(self, cid): return self.cards_by_id.get(cid, {}).get("name", cid)

    def _toggle_deck_card(self, cid):
        if cid in self.profile.deck: self.profile.deck.remove(cid); self._flash(f"Убрано: {self._card_name(cid)}")
        elif len(self.profile.deck) >= 6: self._flash("Колода полна (6 карт)")
        elif cid in self.profile.owned_cards: self.profile.deck.append(cid); self._flash(f"Добавлено: {self._card_name(cid)}")

    def _toggle_deck_util(self, uid):
        if uid in self.profile.utils: self.profile.utils.remove(uid); self._flash("Убрано из утилит")
        elif len(self.profile.utils) >= 3: self._flash("3 утилиты максимум")
        elif uid in self.profile.owned_utils: self.profile.utils.append(uid); self._flash("Добавлено в утилиты")

    def _buy(self, item):
        if self.profile.money < item["price"]: play_game_sound("error"); self._flash("Не хватает денег"); return
        self.profile.money -= item["price"]; self.profile.add_card(item["id"])
        self.shop_items = [x for x in self.shop_items if x["id"] != item["id"]]
        self._flash(f"Куплено: {self._card_name(item['id'])}"); play_game_sound("buy"); play_game_sound("coin")

    def _go_next(self):
        play_game_sound("ui_click")
        try: self.profile.save()
        except Exception as e: print(f"[intermission] save error: {e}")
        try:
            from GameView import GameView; self.window.show_view(GameView(profile=self.profile, night=self.next_night))
        except Exception:
            import traceback; traceback.print_exc(); from MainMenu import MainMenu; self.window.show_view(MainMenu())

    def on_draw(self):
        self._btn_rects = []; self.clear()
        w, h = self.window.width, self.window.height; s = h / 1080
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (8, 8, 12))
        arcade.draw_lbwh_rectangle_filled(0, h - int(100 * s), w, int(100 * s), (18, 12, 12))
        arcade.draw_lbwh_rectangle_filled(0, h - int(100 * s), w, 2, (150, 40, 40))
        arcade.draw_text(f"НОЧЬ {self.next_night}", w / 2, h - int(40 * s), (220, 60, 60), 30 * s, font_name=FONT_TITLE, anchor_x="center")
        arcade.draw_text(f"УР {self.profile.level}", 30 * s, h - int(55 * s), (255, 200, 80), 18 * s, font_name=FONT_UI)
        arcade.draw_text(f"XP {self.profile.xp}/{self.profile.xp_to_next()}", 30 * s, h - int(78 * s), (180, 180, 180), 14 * s, font_name=FONT_UI)
        arcade.draw_text(f"$ {self.profile.money}", w - 30 * s, h - int(55 * s), (200, 220, 100), 22 * s, font_name=FONT_UI, anchor_x="right")
        arcade.draw_text(f"HP {self.profile.max_hp}   EN {self.profile.max_energy}", w - 30 * s, h - int(78 * s), (200, 100, 100), 14 * s, font_name=FONT_UI, anchor_x="right")
        if self.last_rewards:
            r = self.last_rewards; txt = f"+{r.get('money', 0)}$   +{r.get('xp', 0)} XP"
            if r.get("cards"): txt += "   карты: " + ", ".join(self._card_name(c) for c in r["cards"])
            arcade.draw_text(txt, w / 2, h - int(130 * s), (200, 200, 150), 15 * s, font_name=FONT_UI, anchor_x="center")
            if r.get("leveled"): arcade.draw_text(f"УРОВЕНЬ {r.get('new_level', 0)}!", w / 2, h - int(165 * s), (255, 220, 60), 22 * s, font_name=FONT_TITLE, anchor_x="center")
        
        self._draw_tabs(w, h, s)
        content_y = h - int(230 * s)
        if self.tab == "deck": self._draw_deck_tab(w, content_y, s)
        else: self._draw_shop_tab(w, content_y, s)
        
        nx_w, nx_h = int(260 * s), int(64 * s); nx_x, nx_y = w - nx_w - int(40 * s), int(40 * s)
        arcade.draw_lbwh_rectangle_filled(nx_x, nx_y, nx_w, nx_h, (40, 10, 10, 255))
        arcade.draw_lbwh_rectangle_outline(nx_x, nx_y, nx_w, nx_h, (200, 40, 40, 255), 3)
        arcade.draw_text(f"НОЧЬ {self.next_night}  →", nx_x + nx_w / 2, nx_y + nx_h / 2, arcade.color.WHITE, 22 * s, font_name=FONT_TITLE, anchor_x="center", anchor_y="center")
        self._btn_rects.append(("next", (nx_x, nx_y, nx_w, nx_h), None))
        
        if self.message and self.message_age < 2.0:
            alpha = 255 if self.message_age < 1.5 else _clamp255(255 * (2.0 - self.message_age) / 0.5)
            arcade.draw_text(self.message, w / 2, int(130 * s), (255, 220, 100, alpha), 18 * s, font_name=FONT_UI, anchor_x="center")

    def _draw_tabs(self, w, h, s):
        tab_y, tw, th, cx = h - int(200 * s), 180 * s, 44 * s, w / 2
        for i, (name, label) in enumerate([("deck", "КОЛОДА"), ("shop", "ЛАВКА")]):
            x = cx - tw - 10 * s + i * (tw + 20 * s); active = name == self.tab
            bg, border = ((60, 20, 20), (255, 80, 80)) if active else ((25, 20, 25), (80, 80, 90))
            arcade.draw_lbwh_rectangle_filled(x, tab_y, tw, th, bg); arcade.draw_lbwh_rectangle_outline(x, tab_y, tw, th, border, 2)
            arcade.draw_text(label, x + tw / 2, tab_y + th / 2, arcade.color.WHITE if active else (150, 150, 150), 18 * s, font_name=FONT_UI, anchor_x="center", anchor_y="center")
            self._btn_rects.append(("tab", (x, tab_y, tw, th), name))

    def _draw_grid_item(self, x, y, cw, ch, info, in_deck, border_color, is_util=False):
        s = self.window.height / 1080
        bg = (40, 35, 25) if is_util else ((40, 25, 25) if in_deck else (25, 25, 30))
        arcade.draw_lbwh_rectangle_filled(x, y, cw, ch, bg); arcade.draw_lbwh_rectangle_outline(x, y, cw, ch, (255, 200, 100) if in_deck else border_color, 2)
        arcade.draw_text(info.get("name", ""), x + cw / 2, y + ch - (16 if is_util else 18) * s, arcade.color.WHITE, 11 * s, font_name=FONT_UI, anchor_x="center", width=int(cw - 8 * s), align="center")
        if is_util: arcade.draw_text(f"мана {info.get('cost', 0)}", x + cw / 2, y + 8 * s, (100, 220, 255), 11 * s, font_name=FONT_UI, anchor_x="center")
        else:
            arcade.draw_text(f"HP {info.get('hp', 0)}  АТК {info.get('attack', 0)}", x + cw / 2, y + 30 * s, (200, 200, 200), 11 * s, font_name=FONT_UI, anchor_x="center")
            arcade.draw_text(f"мана {info.get('cost', 1)}", x + cw / 2, y + 8 * s, (150, 200, 255), 11 * s, font_name=FONT_UI, anchor_x="center")
        if in_deck: arcade.draw_text("✓", x + cw - 10 * s, y + ch - 14 * s, (120, 255, 120), 16 * s, font_name=FONT_UI, anchor_x="right")

    def _draw_deck_tab(self, w, content_y, s):
        arcade.draw_text(f"МОИ КАРТЫ   ({len(self.profile.deck)}/6 в колоде)", 40 * s, content_y, (255, 200, 80), 16 * s, font_name=FONT_UI)
        cw, ch, gap, cols, x0, y0 = int(CARD_W * s), int(CARD_H * s), int(14 * s), 4, 40 * s, content_y - int(40 * s) - int(CARD_H * s)
        for i, cid in enumerate(self.profile.owned_cards):
            col, row = i % cols, i // cols
            x, y = x0 + col * (cw + gap), y0 - row * (ch + gap)
            if y + ch < int(200 * s): break
            info = self.cards_by_id.get(cid, {}); in_deck = cid in self.profile.deck
            self._draw_grid_item(x, y, cw, ch, info, in_deck, RARITY_COLOR.get(info.get("rarity", "common"), (170, 170, 170)))
            self._btn_rects.append(("card", (x, y, cw, ch), cid))
        ux0 = w * 0.55
        arcade.draw_text(f"МОИ УТИЛИТЫ   ({len(self.profile.utils)}/3)", ux0, content_y, (255, 200, 80), 16 * s, font_name=FONT_UI)
        uw, uh, ucols, uy0 = int(UTIL_W * s), int(UTIL_H * s), 3, content_y - int(40 * s) - int(UTIL_H * s)
        for i, uid in enumerate(self.profile.owned_utils):
            col, row = i % ucols, i // ucols
            x, y = ux0 + col * (uw + gap), uy0 - row * (uh + gap)
            if y + uh < int(200 * s): break
            info = self.utils_by_id.get(uid, {}); in_deck = uid in self.profile.utils
            self._draw_grid_item(x, y, uw, uh, info, in_deck, (100, 100, 110), is_util=True)
            self._btn_rects.append(("util", (x, y, uw, uh), uid))
        arcade.draw_text("Клик по карте/утилите — добавить или убрать из колоды", 40 * s, int(200 * s), (150, 150, 160), 13 * s, font_name=FONT_UI)

    def _draw_shop_tab(self, w, content_y, s):
        arcade.draw_text("ЛАВКА — обновляется каждую ночь", 40 * s, content_y, (255, 200, 80), 16 * s, font_name=FONT_UI)
        if not self.shop_items: arcade.draw_text("Всё распродано.", w / 2, content_y - int(120 * s), (150, 150, 150), 22 * s, font_name=FONT_UI, anchor_x="center"); return
        cw, ch, gap = int(CARD_W * s) + int(30 * s), int(CARD_H * s) + int(60 * s), int(20 * s)
        start_x = (w - (len(self.shop_items) * cw + (len(self.shop_items) - 1) * gap)) / 2
        for i, item in enumerate(self.shop_items):
            x, y = start_x + i * (cw + gap), content_y - int(40 * s) - ch
            info = self.cards_by_id.get(item["id"], {}); affordable = self.profile.money >= item["price"]
            arcade.draw_lbwh_rectangle_filled(x, y, cw, ch, (35, 25, 20) if affordable else (25, 20, 20))
            arcade.draw_lbwh_rectangle_outline(x, y, cw, ch, RARITY_COLOR.get(info.get("rarity", "common"), (170, 170, 170)), 2)
            arcade.draw_text(info.get("name", item["id"]), x + cw / 2, y + ch - 30 * s, arcade.color.WHITE, 16 * s, font_name=FONT_UI, anchor_x="center", width=int(cw - 20 * s), align="center")
            arcade.draw_text(info.get("rarity", "common"), x + cw / 2, y + ch - 55 * s, RARITY_COLOR.get(info.get("rarity", "common")), 12 * s, font_name=FONT_UI, anchor_x="center")
            arcade.draw_text(f"HP {info.get('hp', 0)}   АТК {info.get('attack', 0)}", x + cw / 2, y + ch - 80 * s, (200, 200, 200), 12 * s, font_name=FONT_UI, anchor_x="center")
            arcade.draw_text(f"мана {info.get('cost', 1)}", x + cw / 2, y + ch - 102 * s, (100, 200, 255), 11 * s, font_name=FONT_UI, anchor_x="center")
            btn_h, btn_y = int(40 * s), y + int(10 * s); btn_color = (100, 180, 100) if affordable else (80, 40, 40)
            arcade.draw_lbwh_rectangle_filled(x + int(10 * s), btn_y, cw - int(20 * s), btn_h, btn_color)
            arcade.draw_lbwh_rectangle_outline(x + int(10 * s), btn_y, cw - int(20 * s), btn_h, (255, 255, 255), 2)
            arcade.draw_text(f"КУПИТЬ  {item['price']}$", x + cw / 2, btn_y + btn_h / 2, arcade.color.WHITE, 13 * s, font_name=FONT_UI, anchor_x="center", anchor_y="center")
            self._btn_rects.append(("buy", (x + int(10 * s), btn_y, cw - int(20 * s), btn_h), item))

    def on_update(self, dt): self.time += dt; self.message_age += dt

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT: return
        for kind, rect, payload in self._btn_rects:
            rx, ry, rw, rh = rect
            if rx <= x <= rx + rw and ry <= y <= ry + rh:
                if kind == "tab": play_game_sound("ui_click"); self.tab = payload
                elif kind == "card": self._toggle_deck_card(payload)
                elif kind == "util": self._toggle_deck_util(payload)
                elif kind == "buy": self._buy(payload)
                elif kind == "next": self._go_next()
                return

    def on_key_press(self, key, modifiers):
        if key in _CONFIRM_KEYS or key == arcade.key.ESCAPE: self._go_next()