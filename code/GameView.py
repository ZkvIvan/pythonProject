import os
import math
import json
import random
from types import SimpleNamespace

import arcade
from arcade import gl

from paths import data, asset
from classes.player import Player
from classes.slot import Slot
from classes.card import Card
from classes.grid import Grid
from Audio import play_game_sound, preload_game_sounds, play_sfx, load_ui_sounds

FONT = "Cyrillic Pixel-7"
CARD_W, CARD_H = 117, 168 
SLOT_W, SLOT_H = 120, 170

def load_tex(*candidates):
    for parts in candidates:
        path = asset(*parts)
        if os.path.exists(path):
            try: return arcade.load_texture(path)
            except: pass
    return None

def draw_tex(tex, x, y, w, h):
    if tex: arcade.draw_texture_rect(tex, arcade.LBWH(x, y, w, h))

class GameView(arcade.View):
    def __init__(self, hero_id="knight", player_name="Странник", night=1):
        super().__init__()
        self.time = 0.0
        self._lay = None
        self._lay_key = None
        preload_game_sounds()

        self.hero_id = hero_id
        self.player_name = player_name
        self.night = night
        self.phase = "player" 
        self.phase_timer = 0.0
        self.fight_col = 2
        self.winner = None
        self.active_util_idx = None
        
        self.is_tutorial = (self.night == 1)
        self.tutorial_step = 0
        
        self.banner_x = -1000
        self.banner_phase = "idle"
        self.banner_timer = 0.0
        self.banner_scale = 1.0

        self.card_sprite_list = arcade.SpriteList()
        self.slot_sprite_list = arcade.SpriteList()
        self.hand_sprite_list = arcade.SpriteList()
        self.discard_pile = []

        self.player = Player(self)
        self.enemy = Player(self)
        self.enemy.hp = 10 if self.is_tutorial else 30 + (self.night * 10)

        self.icon_hp = load_tex(("images", "icons", "hp_icon.png"))
        self.icon_dmg = load_tex(("images", "icons", "damage_icon.png"))
        self.icon_energy = load_tex(("images", "icons", "energy_icon.png"))
        self.card_back = load_tex(("images", "Cards", "blank_card.png"), ("images", "blank_card.png"))
        self.bg_texture = load_tex(("images", "background_table.png"))
        self.player_avatar = load_tex(("images", "player", "avatar.png"), ("images", "avatar.png"))
        self.enemy_portrait = load_tex(("images", "enemy", "boss.png"))

        self.grid = Grid(self, 9, 4)
        for i in range(2, 8):
            self.grid.add_slot(i, 1, Slot(self))
            self.grid.add_slot(i, 3, Slot(self))

        try:
            with open(data("cards.json"), "r", encoding="utf-8") as f: self.cards_data = json.load(f)
            with open(data("utilities.json"), "r", encoding="utf-8") as f: self.utilities_data = json.load(f)
            with open(data("dialogs.json"), "r", encoding="utf-8") as f: self.dialogs = json.load(f)
            with open(data("characters.json"), "r", encoding="utf-8") as f:
                chars = json.load(f)
                self.hero_data = next((c for c in chars if c["id"] == self.hero_id), chars[0])
        except Exception as e:
            print(f"Ошибка загрузки JSON: {e}")
            self.cards_data, self.utilities_data, self.dialogs = [], [], {"enemies":[]}
            self.hero_data = {"deck": ["01", "02", "03"]}

        self.cards_by_id = {c["id"]: c for c in self.cards_data}
        self.current_dialog = self.dialogs["tutorial"]["intro"] if self.is_tutorial else random.choice(self.dialogs["before_night"])
        self.dialog_timer = 6.0 # УВЕЛИЧЕНО ДО 6 СЕКУНД
        self._draw_initial_hand()

    @property
    def lay(self):
        w, h = self.window.width, self.window.height
        if self._lay_key != (w, h):
            self._lay = self._compute_layout(w, h)
            self._lay_key = (w, h)
        return self._lay

    def _compute_layout(self, w, h):
        s = h / 1080
        L = SimpleNamespace(w=w, h=h, s=s)
        L.top_h = 195 * s; L.bot_h = 215 * s
        L.mid_y0 = L.bot_h; L.mid_y1 = h - L.top_h; L.mid = (L.mid_y0 + L.mid_y1) / 2
        L.tx0, L.tx1 = 0.112 * w, 0.885 * w
        L.left_w = L.tx0 + 190 * s; L.wavy_x = L.tx0 + 18 * s
        L.turn_cx, L.turn_cy, L.turn_r = (L.tx0 + L.left_w) / 2, L.mid, 60 * s
        L.btn_w, L.btn_h = 160 * s, 45 * s
        L.btn_x = L.turn_cx - L.btn_w / 2; L.btn_y = L.turn_cy - L.turn_r - 60 * s
        L.panel_w = 270 * s; L.panel_h = min(520 * s, (L.mid_y1 - L.mid_y0) - 30 * s)
        L.panel_x = w - L.panel_w - 14 * s; L.panel_y = L.mid - L.panel_h / 2
        L.disc_w, L.disc_h = 90 * s, 126 * s
        L.disc_x = L.panel_x - 20 * s - L.disc_w; L.disc_y = L.mid - L.disc_h / 2
        board_x1 = L.disc_x - 25 * s
        first = L.left_w + SLOT_W * s / 2 + 8 * s
        last = board_x1 - SLOT_W * s / 2
        L.slot_x0 = first; L.slot_step = (last - first) / 5
        row_off = (SLOT_H * s + 110 * s) / 2
        L.enemy_row_y = L.mid + row_off; L.player_row_y = L.mid - row_off
        L.sep1, L.sep2 = 0.28 * w, 0.475 * w
        L.util_x = L.sep1 + 0.012 * w
        L.hand_x0, L.hand_x1 = L.sep2 + 0.012 * w, 0.985 * w
        L.e_util_x = 0.25 * w; L.e_hand_x0, L.e_hand_x1 = 0.62 * w, 0.985 * w
        return L

    def _card_at(self, col, row):
        for slot in self.slot_sprite_list:
            if slot.grid_x == col and slot.grid_y == row: return slot.card
        return None

    def _cleanup_if_dead(self, card):
        if card is None or card.hp > 0: return
        if card in self.card_sprite_list: self.card_sprite_list.remove(card)
        if card.slot and card.slot.card is card: card.slot.remove_card()
        if card.player == self.player: self.discard_pile.append(card)

    def _check_game_over(self):
        if self.phase == "over": return True
        if self.enemy.hp <= 0:
            self.phase = "over"
            self.winner = "ПОБЕДА!"
            play_game_sound("victory")
            if self.is_tutorial:
                self.current_dialog = self.dialogs["tutorial"]["victory"]
                self.dialog_timer = 6.0
                self.is_tutorial = False
            else:
                if self.night >= 5:
                    import pyglet
                    def go_choice(dt):
                        from FinalChoiceView import FinalChoiceView
                        self.window.show_view(FinalChoiceView(self.player_name, len(self.player.cards)))
                    pyglet.clock.schedule_once(go_choice, 3.0)
                else:
                    import pyglet
                    def go_next(dt):
                        self.window.show_view(GameView(self.hero_id, self.player_name, self.night + 1))
                    pyglet.clock.schedule_once(go_next, 3.0)
        elif self.player.hp <= 0:
            self.phase, self.winner = "over", "ПОРАЖЕНИЕ"
            play_game_sound("defeat")
        return self.phase == "over"

    def start_enemy_turn(self):
        if self.player.active: self.player.active.deselect(); self.player.active = None
        if self.active_util_idx is not None: self.active_util_idx = None
        self.phase = "enemy"
        self.phase_timer = 0.0
        self.enemy.energy = self.enemy.max_energy
        if not self.is_tutorial:
            self.current_dialog = random.choice(self.dialogs["enemies"])
            self.dialog_timer = 6.0

    def enemy_take_action(self):
        if self.enemy.energy <= 0 or not self.enemy.hand: return False
        free = [s for s in self.slot_sprite_list if s.grid_y == 3 and s.card is None]
        if not free: return False
        info = self.enemy.hand.pop(0)
        card = Card(self, self.enemy, hp=info["hp"], strength=info["attack"], texture_name=info["id"])
        self.enemy.cards.append(card)
        self.card_sprite_list.append(card)
        random.choice(free).add_card(card)
        self.enemy.energy -= 1
        play_game_sound("enemy_place")
        return True

    def start_fight(self):
        self.phase = "fight"
        self.phase_timer = 0.0
        self.fight_col = 2
        play_game_sound("fight_start")
        self.banner_phase = "in"
        self.banner_x = -900 * self.lay.s
        self.banner_scale = 1.0
        if self.is_tutorial:
            self.current_dialog = self.dialogs["tutorial"]["fight"]
            self.dialog_timer = 6.0

    def resolve_column(self, col):
        p, e = self._card_at(col, 1), self._card_at(col, 3)
        if p and e:
            play_game_sound("hit"); p.deal_damage(e); e.deal_damage(p)
        elif p:
            self.enemy.hp = max(0, self.enemy.hp - p.strength); play_game_sound("hero_hit")
        elif e:
            self.player.hp = max(0, self.player.hp - e.strength); play_game_sound("hero_hit")
        died = any(c is not None and c.hp <= 0 for c in (p, e))
        self._cleanup_if_dead(p); self._cleanup_if_dead(e)
        if died: play_game_sound("card_death")
        self._check_game_over()

    def start_player_turn(self):
        self.phase = "player"
        self.phase_timer = 0.0
        self.player.energy = self.player.max_energy
        play_game_sound("turn_start")

    def _draw_initial_hand(self):
        if not self.cards_data: return
        for card_id in self.hero_data.get("deck", ["01", "02", "03", "04", "05", "06"]):
            info = next((c for c in self.cards_data if c["id"] == card_id), self.cards_data[0])
            card = Card(self, self.player, hp=info["hp"], strength=info["attack"], texture_name=info["id"], description=info.get("text", ""))
            self.player.hand.append(card)
            self.hand_sprite_list.append(card)

        self.enemy.hand = random.sample(self.cards_data, 6)

    def _execute_utility(self, index):
        if index >= len(self.utilities_data): return
        util = self.utilities_data[index]
        cost = util.get("cost", 1)
        if self.player.energy < cost:
            play_game_sound("error"); return
        self.player.energy -= cost
        play_game_sound("card_place")
        if "heal" in util["id"]: self.player.hp = min(self.player.max_hp, self.player.hp + 5)
        elif "fireball" in util["id"]: self.enemy.hp = max(0, self.enemy.hp - 3); self._check_game_over()

    def update_tutorial(self):
        if not self.is_tutorial: return
        if self.tutorial_step == 0 and self.player.active is not None:
            self.current_dialog = self.dialogs["tutorial"]["cards"]
            self.dialog_timer = 6.0; self.tutorial_step = 1
        elif self.tutorial_step == 1 and len(self.player.hand) < 6:
            self.current_dialog = self.dialogs["tutorial"]["end_turn"]
            self.dialog_timer = 6.0; self.tutorial_step = 2
        elif self.tutorial_step == 2 and self.phase == "enemy":
            self.tutorial_step = 3
        elif self.tutorial_step == 3 and self.phase == "fight":
            self.current_dialog = self.dialogs["tutorial"]["abilities"]
            self.dialog_timer = 6.0; self.tutorial_step = 4

    def _draw_bar(self, x, y, width, height, current, max_val, color):
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (30, 30, 35))
        if current > 0: arcade.draw_lbwh_rectangle_filled(x, y, width * (max(0, current) / max_val), height, color)
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, (100, 100, 100), 2)

    def _apply_card_scale(self, card):
        s = self.lay.s
        target = s * 1.1 if card.is_selected else s
        if getattr(card, "_applied_scale", None) != target:
            card.scale = target; card._applied_scale = target

    @staticmethod
    def _hp_color(ratio):
        return (arcade.color.WHITE if ratio > 0.6 else arcade.color.YELLOW_ORANGE if ratio > 0.3 else arcade.color.DARK_RED)

    def draw_turn_indicator(self):
        L = self.lay; s, cx, cy, radius = L.s, L.turn_cx, L.turn_cy, L.turn_r
        if self.phase == "player":
            pulse = math.sin(self.time * 3)
            arcade.draw_circle_filled(cx, cy, radius + (pulse * 10 * s), (255, 200, 0, int(100 + pulse * 50)))
            arcade.draw_circle_outline(cx, cy, radius, (255, 255, 255), 4)
            arcade.draw_text("ВАШ\nХОД", cx, cy, arcade.color.WHITE, 22 * s, font_name=FONT, align="center", anchor_x="center", anchor_y="center", multiline=True, width=int(radius*2))
            fill, border, label = (60, 40, 20), (200, 150, 50), "ЗАВЕРШИТЬ"
        else:
            arcade.draw_circle_filled(cx, cy, radius, (150, 30, 30, 150))
            arcade.draw_circle_outline(cx, cy, radius, (255, 50, 50), 4)
            arcade.draw_text("ХОД\nВРАГА" if self.phase=="enemy" else "БОЙ!", cx, cy, arcade.color.LIGHT_GRAY, 18 * s, font_name=FONT, align="center", anchor_x="center", anchor_y="center", multiline=True, width=int(radius*2))
            fill, border, label = (50, 10, 10), (150, 50, 50), "ОЖИДАНИЕ"
        arcade.draw_lbwh_rectangle_filled(L.btn_x, L.btn_y, L.btn_w, L.btn_h, fill)
        arcade.draw_lbwh_rectangle_outline(L.btn_x, L.btn_y, L.btn_w, L.btn_h, border, 2)
        arcade.draw_text(label, cx, L.btn_y + L.btn_h / 2, arcade.color.WHITE if self.phase=="player" else arcade.color.GRAY, 14 * s, font_name=FONT, anchor_x="center", anchor_y="center")

    def draw_enemy_hud(self):
        L = self.lay; s, w, h, hud_h = L.s, L.w, L.h, L.top_h; base = h - hud_h
        arcade.draw_lbwh_rectangle_filled(0, base, w, hud_h, (15, 15, 20))
        arcade.draw_lbwh_rectangle_filled(0, base, w, 2, (100, 100, 100))
        
        icon_x, bar_y = 30 * s, base + 50 * s; bar_x, bar_w = icon_x + 32 * s, 250 * s
        arcade.draw_text("ВРАГ", icon_x, bar_y + 60 * s, arcade.color.WHITE, 22 * s, font_name=FONT)
        draw_tex(self.icon_hp, icon_x, bar_y + 29 * s, 27 * s, 27 * s)
        draw_tex(self.icon_energy, icon_x, bar_y - 6 * s, 27 * s, 27 * s)
        self._draw_bar(bar_x, bar_y + 30 * s, bar_w, 25 * s, self.enemy.hp, self.enemy.max_hp, arcade.color.RED)
        self._draw_bar(bar_x, bar_y - 5 * s, bar_w, 25 * s, self.enemy.energy, self.enemy.max_energy, arcade.color.CYAN)

        uw, uh = 80 * s, 110 * s; uy = base + (hud_h - uh) / 2
        for i in range(3):
            ux = L.e_util_x + i * (uw + 10 * s)
            arcade.draw_lbwh_rectangle_filled(ux, uy, uw, uh, (30, 30, 35))
            arcade.draw_lbwh_rectangle_outline(ux, uy, uw, uh, (100, 100, 100), 2)

        if self.enemy_portrait:
            p_h = hud_h; p_w = p_h * (self.enemy_portrait.width / self.enemy_portrait.height)
            p_x, p_y = (w / 2) - (p_w / 2), h - p_h
            arcade.draw_texture_rect(self.enemy_portrait, arcade.LBWH(p_x, p_y, p_w, p_h))
            # БЕЛАЯ РАМКА ВРАГА
            arcade.draw_lbwh_rectangle_outline(p_x, p_y, p_w, p_h, arcade.color.WHITE, 4)

        step = (L.e_hand_x1 - L.e_hand_x0) / 6; ch = 150 * s; cw = ch * (768 / 1152); cy = base + hud_h / 2
        for i in range(6):
            cx = L.e_hand_x0 + step * (i + 0.5)
            if self.card_back: draw_tex(self.card_back, cx - cw / 2, cy - ch / 2, cw, ch)

    def draw_player_hud(self):
        L = self.lay; s, w, hud_h = L.s, L.w, L.bot_h
        arcade.draw_lbwh_rectangle_filled(0, 0, w, hud_h, (15, 15, 20))
        arcade.draw_lbwh_rectangle_filled(0, hud_h, w, 2, (100, 100, 100))
        
        avatar_size = 130 * s; avatar_x, avatar_y = 20 * s, 35 * s
        frame_color = self._hp_color(self.player.hp / self.player.max_hp)
        if self.player_avatar: draw_tex(self.player_avatar, avatar_x, avatar_y, avatar_size, avatar_size)
        else: arcade.draw_lbwh_rectangle_filled(avatar_x, avatar_y, avatar_size, avatar_size, (30, 30, 35))
        arcade.draw_lbwh_rectangle_outline(avatar_x, avatar_y, avatar_size, avatar_size, frame_color, 4)
        arcade.draw_text("ГЕРОЙ", avatar_x, avatar_y + avatar_size + 5 * s, frame_color, 18 * s, font_name=FONT)

        icon_x = avatar_x + avatar_size + 15 * s; bar_x, bar_w = icon_x + 32 * s, 190 * s
        draw_tex(self.icon_hp, icon_x, avatar_y + 84 * s, 27 * s, 27 * s)
        self._draw_bar(bar_x, avatar_y + 85 * s, bar_w, 25 * s, self.player.hp, self.player.max_hp, arcade.color.RED)
        draw_tex(self.icon_energy, icon_x, avatar_y + 44 * s, 27 * s, 27 * s)
        self._draw_bar(bar_x, avatar_y + 45 * s, bar_w, 25 * s, self.player.energy, self.player.max_energy, arcade.color.CYAN)

        util_w, util_h, util_y = 90 * s, 130 * s, 40 * s
        arcade.draw_text("УТИЛИТЫ", L.util_x, hud_h - 25 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name=FONT)
        for i in range(3):
            ux = L.util_x + i * (util_w + 10 * s)
            if self.card_back: draw_tex(self.card_back, ux, util_y, util_w, util_h)
            else: arcade.draw_lbwh_rectangle_filled(ux, util_y, util_w, util_h, (40, 40, 50))
            border_col = arcade.color.GOLD if self.active_util_idx == i else (100, 100, 100)
            arcade.draw_lbwh_rectangle_outline(ux, util_y, util_w, util_h, border_col, 3 if self.active_util_idx==i else 2)
            if i < len(self.utilities_data):
                arcade.draw_text(self.utilities_data[i]["name"], ux + util_w/2, util_y + util_h/2, arcade.color.WHITE, 12 * s, font_name=FONT, width=int(util_w - 10*s), align="center", anchor_x="center", anchor_y="center", multiline=True)
                arcade.draw_text(f"{self.utilities_data[i]['cost']}", ux + util_w - 15*s, util_y + util_h - 20*s, arcade.color.CYAN, 16 * s, font_name=FONT, anchor_x="center", anchor_y="center")
        arcade.draw_text("РУКА", L.hand_x0, hud_h - 25 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name=FONT)

    def draw_hand(self):
        L = self.lay; s = L.s; num_slots = 6; step = (L.hand_x1 - L.hand_x0) / num_slots
        card_w, card_h = CARD_W * s, CARD_H * s; start_x, cy = L.hand_x0 + step / 2, 88 * s
        for i in range(num_slots):
            cx = start_x + i * step; left, bottom = cx - card_w / 2, cy - card_h / 2
            arcade.draw_lbwh_rectangle_filled(left, bottom, card_w, card_h, (10, 10, 12, 150))
            arcade.draw_lbwh_rectangle_outline(left, bottom, card_w, card_h, (60, 60, 60), 2)
        for i, card in enumerate(self.player.hand):
            self._apply_card_scale(card); card.center_x = start_x + i * step; card.center_y = cy
        self.hand_sprite_list.draw(filter=gl.NEAREST)
        for card in self.player.hand: card.draw_highlight()

    def draw_card_info(self):
        L = self.lay; s = L.s; x, y, pw, ph = L.panel_x, L.panel_y, L.panel_w, L.panel_h
        card = self.player.active
        arcade.draw_lbwh_rectangle_filled(x, y, pw, ph, (15, 15, 20, 240))
        arcade.draw_lbwh_rectangle_outline(x, y, pw, ph, (100, 100, 100), 2)
        if not card and self.active_util_idx is None: return

        top = y + ph
        if card:
            info = self.cards_by_id.get(card.texture_name, {})
            arcade.draw_text(info.get("name", ""), x + 15 * s, top - 40 * s, arcade.color.WHITE, 22 * s, font_name=FONT)
            draw_tex(self.icon_hp, x + 15 * s, top - 128 * s, 30 * s, 30 * s)
            arcade.draw_text(f"{card.hp}", x + 52 * s, top - 124 * s, arcade.color.RED, 22 * s, font_name=FONT)
            draw_tex(self.icon_dmg, x + 100 * s, top - 128 * s, 30 * s, 30 * s)
            arcade.draw_text(f"{card.strength}", x + 137 * s, top - 124 * s, arcade.color.GOLD, 22 * s, font_name=FONT)
            full = info.get("text", card.description) or ""
            mech, _, lore = full.partition("\n\n")
            arcade.draw_text(mech, x + 15 * s, top - 160 * s, (235, 235, 235), 15 * s, font_name=FONT, width=int(pw - 30*s), multiline=True)
        elif self.active_util_idx is not None:
            util = self.utilities_data[self.active_util_idx]
            arcade.draw_text(util["name"], x + 15 * s, top - 40 * s, arcade.color.WHITE, 22 * s, font_name=FONT)
            draw_tex(self.icon_energy, x + 15 * s, top - 128 * s, 30 * s, 30 * s)
            arcade.draw_text(f"{util['cost']}", x + 52 * s, top - 124 * s, arcade.color.CYAN, 22 * s, font_name=FONT)
            arcade.draw_text(util.get("text", ""), x + 15 * s, top - 160 * s, (235, 235, 235), 15 * s, font_name=FONT, width=int(pw - 30*s), multiline=True)

    def draw_dialog_box(self):
        if self.dialog_timer <= 0: return
        L = self.lay; s = L.s
        box_w, box_h = 800 * s, 150 * s
        box_x = (L.w / 2) - (box_w / 2)
        box_y = L.mid_y1 - box_h - 20 * s
        arcade.draw_lbwh_rectangle_filled(box_x, box_y, box_w, box_h, (10, 5, 5, 240))
        # БЕЛАЯ РАМКА ДИАЛОГА
        arcade.draw_lbwh_rectangle_outline(box_x, box_y, box_w, box_h, arcade.color.WHITE, 2)
        arcade.draw_text(self.current_dialog, box_x + box_w / 2, box_y + box_h / 2, (220, 220, 220), 22 * s, font_name=FONT, width=int(box_w - 40 * s), align="center", anchor_x="center", anchor_y="center", multiline=True)

    def draw_banner(self):
        if self.banner_phase == "idle": return
        L = self.lay; s = L.s
        arcade.draw_lbwh_rectangle_filled(0, 0, L.w, L.h, (0, 0, 0, 120))
        base_w, base_h = 900 * s, 220 * s; w = base_w * self.banner_scale; h = base_h * self.banner_scale; y = L.mid - h / 2; x = self.banner_x + (base_w - w) / 2
        arcade.draw_lbwh_rectangle_filled(x, y, w, h, (20, 5, 5, 240))
        arcade.draw_lbwh_rectangle_outline(x, y, w, h, (150, 30, 30), 8)
        font_size = int(120 * s * self.banner_scale); cx, cy = x + w / 2, y + h / 2
        arcade.draw_text("БОЙ!", cx + 6*s, cy - 6*s, arcade.color.BLACK, font_size, font_name=FONT, anchor_x="center", anchor_y="center")
        arcade.draw_text("БОЙ!", cx, cy, arcade.color.RED, font_size, font_name=FONT, anchor_x="center", anchor_y="center")

    def on_draw(self):
        self.clear()
        L = self.lay
        if self.bg_texture:
            scale_bg = max(L.w / self.bg_texture.width, L.h / self.bg_texture.height)
            arcade.draw_texture_rect(self.bg_texture, arcade.LBWH((L.w - self.bg_texture.width*scale_bg)/2, (L.h - self.bg_texture.height*scale_bg)/2, self.bg_texture.width*scale_bg, self.bg_texture.height*scale_bg))
        
        self.grid.update()
        for slot in self.slot_sprite_list: slot.draw()
        for card in self.card_sprite_list:
            self._apply_card_scale(card); card.draw_highlight()
        self.card_sprite_list.draw(filter=gl.NEAREST)

        self.draw_turn_indicator()
        self.draw_discard()
        self.draw_enemy_hud()
        self.draw_player_hud()
        self.draw_hand()
        self.draw_card_info()
        self.draw_dialog_box()
        self.draw_banner()

    def on_update(self, delta_time):
        self.time += delta_time
        if self.dialog_timer > 0: self.dialog_timer -= delta_time
        self.update_tutorial()

        if self.phase == "enemy":
            self.phase_timer += delta_time
            if self.phase_timer >= 0.8:
                self.phase_timer = 0.0
                if not self.enemy_take_action(): self.start_fight()
        elif self.phase == "fight":
            if self.banner_phase == "in":
                target_x = (self.lay.w - 900 * self.lay.s) / 2
                self.banner_x += (target_x - self.banner_x) * 6 * delta_time
                if abs(self.banner_x - target_x) < 5: self.banner_x = target_x; self.banner_phase = "slow"; self.banner_timer = 0.0
            elif self.banner_phase == "slow":
                self.banner_timer += delta_time
                self.banner_scale = 1.0 + math.sin(self.banner_timer * 8) * 0.06
                if self.banner_timer > 1.2: self.banner_phase = "out"
            elif self.banner_phase == "out":
                self.banner_scale = 1.0; self.banner_x += 3500 * self.lay.s * delta_time
                if self.banner_x > self.lay.w: self.banner_phase = "idle"

            self.phase_timer += delta_time
            if self.phase_timer >= 0.8:
                self.phase_timer = 0.0
                self.resolve_column(self.fight_col)
                if self.phase == "over": return
                self.fight_col += 1
                if self.fight_col > 7: self.start_player_turn()

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT or self.phase != "player": return
        L = self.lay

        if L.btn_x <= x <= L.btn_x + L.btn_w and L.btn_y <= y <= L.btn_y + L.btn_h:
            play_game_sound("end_turn"); self.start_enemy_turn(); return

        util_w, util_h, util_y = 90 * L.s, 130 * L.s, 40 * L.s
        for i in range(3):
            ux = L.util_x + i * (util_w + 10 * L.s)
            if ux <= x <= ux + util_w and util_y <= y <= util_y + util_h:
                if i >= len(self.utilities_data): return
                if self.active_util_idx == i:
                    self._execute_utility(i); self.active_util_idx = None
                else:
                    if self.player.active: self.player.active.deselect(); self.player.active = None
                    self.active_util_idx = i; play_game_sound("card_select")
                return

        hit_hand = arcade.get_sprites_at_point((x, y), self.hand_sprite_list)
        if hit_hand:
            card = hit_hand[0]; was_active = self.player.active == card
            if self.player.active: self.player.active.deselect()
            self.player.active = None
            if self.active_util_idx is not None: self.active_util_idx = None
            if not was_active: self.player.active = card; card.select()
            play_game_sound("card_deselect" if was_active else "card_select"); return

        hit_slots = arcade.get_sprites_at_point((x, y), self.slot_sprite_list)
        if hit_slots:
            slot = hit_slots[0]; card = self.player.active
            if not (card and card in self.player.hand): return
            if slot.grid_y != 1 or slot.card is not None: play_game_sound("error"); return
            if self.player.energy <= 0: play_game_sound("error"); return

            self.player.hand.remove(card); self.hand_sprite_list.remove(card)
            self.player.cards.append(card); self.card_sprite_list.append(card)
            slot.add_card(card); card.deselect(); self.player.active = None
            self.player.energy -= 1; play_game_sound("card_place")

    def draw_discard(self):
        L = self.lay; s = L.s
        x, y, w, h = L.disc_x, L.disc_y, L.disc_w, L.disc_h
        arcade.draw_lbwh_rectangle_filled(x, y, w, h, (30, 10, 10, 200))
        arcade.draw_lbwh_rectangle_outline(x, y, w, h, (120, 50, 50), 2)
        arcade.draw_text("СБРОС", x + w / 2, y + h + 10 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name=FONT, anchor_x="center")
        arcade.draw_text(str(len(self.discard_pile)), x + w / 2, y + h / 2, arcade.color.WHITE, 26 * s, font_name=FONT, anchor_x="center", anchor_y="center")