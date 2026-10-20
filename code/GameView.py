import os, math, json, random
from types import SimpleNamespace
import arcade
from arcade import gl
from paths import data, asset
from classes.player import Player
from classes.slot import Slot
from classes.card import Card
from classes.grid import Grid
from Settings import settings
from vfx import VFX
from Audio import play_game_sound, preload_game_sounds, play_sfx, load_ui_sounds
from profile import Profile, starter_utils
from battle_ui import draw_ui
from battle_utils import use_utility

FONT = "Cyrillic Pixel-7"
CARD_W, CARD_H, SLOT_W, SLOT_H = 117, 168, 120, 170
MAX_HAND, MAX_NIGHTS = 6, 5
KEYWORD_ICON = {"poison": "poison", "fire": "fire"}
KEYWORD_NAME = {"poison": "Яд", "fire": "Огонь"}
FALLBACK_PORTRAITS = ["boss", "false_god", "skeleton"]
RARITY = {"common": ("Обычная", (170, 170, 170)), "rare": ("Редкая", (90, 150, 255)), "legendary": ("Легендарная", (255, 200, 50))}
UTIL_TARGETS = {"util_02": "enemy_card", "util_03": "ally_card", "util_06": "ally_card", "util_07": "enemy_card", "util_08": "enemy_card", "util_09": "ally_card", "util_12": "enemy_card", "util_13": "ally_card", "util_16": "enemy_card", "util_17": "enemy_card", "util_18": "enemy_card", "util_21": "enemy_card", "util_26": "ally_card"}
_CONFIRM_KEYS = tuple(v for n in ("ENTER", "RETURN", "NUM_ENTER", "SPACE") if (v := getattr(arcade.key, n, None)) is not None)

def load_tex(*candidates):
    for parts in candidates:
        if os.path.exists(path := asset(*parts)):
            try: return arcade.load_texture(path)
            except Exception: pass
    return None

def scan_enemy_portraits():
    folder = asset("images", "enemy"); found = []
    if os.path.isdir(folder):
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith((".png", ".jpg", ".jpeg")):
                try: found.append(arcade.load_texture(os.path.join(folder, fname)))
                except Exception: pass
    if not found:
        for name in FALLBACK_PORTRAITS:
            if t := load_tex(("images", "enemy", f"{name}.png"), ("images", f"{name}.png")): found.append(t)
    return found

class GameView(arcade.View):
    def __init__(self, profile=None, hero_id=None, player_name=None, night=1):
        super().__init__()
        if profile is None:
            hero_id, player_name = hero_id or "knight", player_name or "Жнец"
            try:
                with open(data("characters.json"), "r", encoding="utf-8") as f: hero = next((h for h in json.load(f) if h["id"] == hero_id), None)
                deck = hero["deck"] if hero else []
            except Exception: deck = []
            profile = Profile.new_game(hero_id, player_name, deck, starter_utils())

        self.profile, self.hero_id, self.player_name, self.night = profile, profile.hero_id, profile.player_name, night
        self.is_boss, self.is_tutorial = night >= MAX_NIGHTS, night == 1
        self.time, self._lay, self._lay_key = 0.0, None, None
        self.vfx = VFX(self)
        self._intro_done = False
        self._shake_cam = arcade.Camera2D() if hasattr(arcade, "Camera2D") else None
        preload_game_sounds()

        self.phase, self.phase_timer, self.fight_col, self.winner = "player", 0.0, 2, None
        self._card_anims = {}
        self.card_sprite_list, self.slot_sprite_list, self.hand_sprite_list = arcade.SpriteList(), arcade.SpriteList(), arcade.SpriteList()
        self.discard_pile = []

        try:
            with open(data("cards.json"), "r", encoding="utf-8") as f: self.cards_data = json.load(f)
            with open(data("utilities.json"), "r", encoding="utf-8") as f: self.utilities_data = json.load(f)
            with open(data("dialogs.json"), "r", encoding="utf-8") as f: self.dialogs = json.load(f)
        except Exception: self.cards_data, self.utilities_data, self.dialogs = [], [], {}
        
        self.cards_by_id, self.utils_by_id = {c["id"]: c for c in self.cards_data}, {u["id"]: u for u in self.utilities_data}

        self.player = Player(self, hero_id=self.hero_id)
        self.player.max_hp, self.player.hp = self.profile.max_hp, self.profile.max_hp
        self.player.max_energy, self.player.energy = self.profile.max_energy, self.profile.max_energy
        self.player.level = self.profile.level
        self.player.init_deck(list(self.profile.deck) or [c["id"] for c in self.cards_data[:6]])

        self.enemy = Player(self)
        if self.is_tutorial: self.enemy.max_hp, self.enemy.max_energy = 10, 2
        elif self.is_boss: self.enemy.max_hp, self.enemy.max_energy = 60, 5
        else: self.enemy.max_hp, self.enemy.max_energy = 30 + night * 5, min(3 + night // 2, 5)
        self.enemy.hp, self.enemy.energy = self.enemy.max_hp, self.enemy.max_energy

        pool = [c["id"] for c in self.cards_data if not self.is_tutorial or c.get("cost", 99) <= 2]
        random.shuffle(pool)
        self.enemy_deck_ids = pool[:12]

        util_ids = list(self.profile.utils) or starter_utils()
        self.player_utilities = [self.utils_by_id.get(u) for u in util_ids[:3]]
        while len(self.player_utilities) < 3: self.player_utilities.append(None)

        self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False
        self._hovered_card, self._hovered_util_idx = None, None
        self._util_rects, self._ability_btn_rect = [], None

        self.dialog_text, self.dialog_age, self.dialog_dur = "", 0.0, 0.0
        self._shown_tutorial, self._dialog_cache, self._dialog_cache_key = set(), None, None

        self.icon_hp, self.icon_dmg, self.icon_energy = load_tex(("images", "icons", "hp_icon.png")), load_tex(("images", "icons", "damage_icon.png")), load_tex(("images", "icons", "energy_icon.png"))
        self.status_icons = {n: load_tex(("images", "icons", f"{n}.png"), ("images", "status", f"{n}.png")) for n in set(KEYWORD_ICON.values())}
        self.card_back, self.bg_texture = load_tex(("images", "Cards", "blank_card.png")), load_tex(("images", "background_table.png"))
        self.player_portrait = load_tex(("images", "players", f"{self.hero_id}.png"), ("images", "players", f"{self.hero_id}.jpg"))
        
        portraits = scan_enemy_portraits()
        self.enemy_portrait = random.choice(portraits) if portraits else None

        self.grid = Grid(self, 9, 4)
        for i in range(2, 8):
            self.grid.add_slot(i, 1, Slot(self))
            self.grid.add_slot(i, 3, Slot(self))

        self.enemy_start_cards = []
        self._draw_initial_hand()
        for card in self.enemy.cards:
            if card.card_id not in self.enemy_start_cards: self.enemy_start_cards.append(card.card_id)

        if self.is_tutorial: self.show_dialog(self.dialogs.get("tutorial", {}).get("intro", ""), 5.0)

    def show_dialog(self, text, duration=4.5):
        if text: self.dialog_text, self.dialog_age, self.dialog_dur = text, 0.0, duration

    def _maybe_tutorial(self, key):
        if not self.is_tutorial or key in self._shown_tutorial: return
        txt = self.dialogs.get("tutorial", {}).get(key, "")
        if txt: self._shown_tutorial.add(key); self.show_dialog(txt, 4.5)

    def _next_enemy_card(self):
        if not self.enemy_deck_ids:
            pool = [c["id"] for c in self.cards_data]; random.shuffle(pool); self.enemy_deck_ids = pool[:12]
        return self.enemy_deck_ids.pop(0) if self.enemy_deck_ids else None

    def _spawn_player_card(self, cid):
        if len(self.player.hand) >= MAX_HAND: return
        if info := self.cards_by_id.get(cid):
            card = Card(self, self.player, info["hp"], info["attack"], cid, info.get("text", ""), info.get("keywords", []), cid)
            self.player.hand.append(card)
            self.hand_sprite_list.append(card)

    def _draw_initial_hand(self):
        for _ in range(MAX_HAND):
            if len(self.player.hand) >= MAX_HAND: break
            if cid := self.player.draw_card_id(): self._spawn_player_card(cid)
        free = [s for s in self.slot_sprite_list if s.grid_y == 3]; random.shuffle(free)
        for i in range(1 if self.is_tutorial else 2):
            if i >= len(free): break
            cid = self._next_enemy_card()
            if not cid or not (info := self.cards_by_id.get(cid)): continue
            card = Card(self, self.enemy, info["hp"], info["attack"], cid, keywords=info.get("keywords", []), card_id=cid)
            self.enemy.cards.append(card); self.card_sprite_list.append(card); free[i].add_card(card)

    @property
    def lay(self):
        w, h = self.window.width, self.window.height
        if self._lay_key != (w, h):
            s = h / 1080
            L = SimpleNamespace(w=w, h=h, s=s, top_h=195*s, bot_h=215*s, mid_y0=215*s, mid_y1=h-195*s, mid=(215*s+h-195*s)/2, tx0=0.112*w, tx1=0.885*w)
            L.left_w, L.wavy_x = L.tx0 + 190 * s, L.tx0 + 18 * s
            L.turn_cx, L.turn_cy, L.turn_r = (L.tx0 + L.left_w) / 2, L.mid, 60 * s
            L.btn_w, L.btn_h = 160 * s, 45 * s
            L.btn_x, L.btn_y = L.turn_cx - L.btn_w / 2, L.turn_cy - L.turn_r - 60 * s
            L.panel_w, L.panel_h = 270 * s, min(520 * s, (L.mid_y1 - L.mid_y0) - 30 * s)
            L.panel_x, L.panel_y = w - L.panel_w - 14 * s, L.mid - L.panel_h / 2
            L.disc_w, L.disc_h = 90 * s, 126 * s
            L.disc_x, L.disc_y = L.panel_x - 20 * s - L.disc_w, L.mid - L.disc_h / 2
            first, last = L.left_w + SLOT_W * s / 2 + 8 * s, (L.disc_x - 25 * s) - SLOT_W * s / 2
            L.slot_x0, L.slot_step = first, (last - first) / 5
            row_off = (SLOT_H * s + 110 * s) / 2
            L.enemy_row_y, L.player_row_y = L.mid + row_off, L.mid - row_off
            L.sep1, L.sep2 = 0.28 * w, 0.475 * w
            L.util_x, L.hand_x0, L.hand_x1 = L.sep1 + 0.012 * w, L.sep2 + 0.012 * w, 0.985 * w
            L.enemy_hero, L.player_hero = (w / 2, h - L.top_h / 2), (85 * s, 100 * s)
            L.p_en_bar = (20 * s + 130 * s + 15 * s + 32 * s, 80 * s, 190 * s, 25 * s)
            L.e_hand_x0, L.e_hand_x1 = 0.62 * w, 0.985 * w
            L.dialog_h, L.dialog_y = 62 * s, L.mid_y1 - 62 * s - 8 * s
            self._lay, self._lay_key = L, (w, h)
        return self._lay

    def _card_at(self, col, row):
        return next((s.card for s in self.slot_sprite_list if s.grid_x == col and s.grid_y == row), None)

    def damage_card(self, card, amount):
        card.take_hit(amount)
        if card.hp <= 0 and self._handle_death(card): self.vfx.card_death(card)

    def _handle_death(self, card):
        if not card: return False
        if card.has_kw("rebirth") and not card.has_rebirthed:
            card.has_rebirthed, card.hp, card.strength, card.poison_turns = True, 1, max(1, card.strength - 1), 0
            self.vfx.float_text(card.center_x, card.center_y + 30 * self.lay.s, "ВОЗРОЖДЕНИЕ", (255, 200, 80)); return False
        slot = card.slot
        if slot: slot.remove_card()
        if card.has_kw("summon") and (info := self.cards_by_id.get("56")):
            mummy = Card(self, card.player, info["hp"], info["attack"], "56", keywords=info.get("keywords", []), card_id="56")
            card.player.cards.append(mummy); self.card_sprite_list.append(mummy)
            if slot: slot.add_card(mummy)
            self.vfx.place(mummy.center_x, mummy.center_y, enemy=(card.player == self.enemy))
        if card in self.card_sprite_list: self.card_sprite_list.remove(card)
        if card in self.player.cards: self.player.cards.remove(card)
        if card in self.enemy.cards: self.enemy.cards.remove(card)
        if card.player == self.player: self.player.discard.append(card.card_id); self.discard_pile.append(card)
        return True

    def _check_game_over(self):
        if self.phase == "over": return True
        if self.enemy.hp <= 0:
            self.phase, self.winner = "over", "ПОБЕДА!"; play_game_sound("victory"); self.vfx.start_game_over(True)
            try:
                xp_gain, money_gain = self.night * 40 + (60 if self.is_boss else 0), self.night * 15 + random.randint(5, 20)
                reward_cards = random.sample(self.enemy_start_cards, min(2, len(self.enemy_start_cards)))
                self.profile.add_money(money_gain); leveled = self.profile.add_xp(xp_gain)
                for cid in reward_cards: self.profile.add_card(cid)
                self.profile.last_rewards = {"money": money_gain, "xp": xp_gain, "cards": reward_cards, "leveled": leveled, "new_level": self.profile.level}
                self.profile.save(); play_game_sound("coin")
                if leveled: play_game_sound("level_up")
            except Exception as e: print(f"[reward] error: {e}")
        elif self.player.hp <= 0:
            self.phase, self.winner = "over", "ПОРАЖЕНИЕ"; play_game_sound("defeat"); self.vfx.start_game_over(False)
        return self.phase == "over"

    def _handle_game_over_click(self):
        if self.vfx.over_t is None or self.vfx.over_t < 0.4: return
        try:
            if self.winner == "ПОБЕДА!":
                self.profile.night = min(MAX_NIGHTS + 1, self.night + 1); self.profile.save()
                if self.night >= MAX_NIGHTS:
                    from FinalChoiceView import FinalChoiceView
                    self.window.show_view(FinalChoiceView(self.player_name, self.profile.level))
                else:
                    from IntermissionView import IntermissionView
                    self.window.show_view(IntermissionView(self.profile, self.night + 1))
            else:
                from MainMenu import MainMenu; self.window.show_view(MainMenu())
        except Exception:
            import traceback; traceback.print_exc()
            from MainMenu import MainMenu; self.window.show_view(MainMenu())

    def start_enemy_turn(self):
        if self.player.active: self.player.active.deselect(); self.player.active = None
        self.pending_util, self._targeting_util = None, False
        for card in self.enemy.cards:
            if card.has_kw("regen") and card.hp > 0: card.hp = min(card.max_hp, card.hp + 1)
            if card.has_kw("magic") and self.player.cards:
                target = random.choice(self.player.cards); target.take_hit(1)
                if target.hp <= 0 and self._handle_death(target): self.vfx.card_death(target)
        self.phase, self.phase_timer, self.enemy.energy = "enemy", 0.0, self.enemy.max_energy
        self.vfx.show_banner("ХОД ВРАГА", (200, 90, 230), 1.2)

    def enemy_take_action(self):
        if self.enemy.energy <= 0 or len(self.enemy.cards) >= 6 or not (free := [s for s in self.slot_sprite_list if s.grid_y == 3 and s.card is None]): return False
        for _ in range(6):
            cid = self._next_enemy_card()
            if not cid or not (info := self.cards_by_id.get(cid)) or info.get("cost", 1) > self.enemy.energy: continue
            card = Card(self, self.enemy, info["hp"], info["attack"], cid, keywords=info.get("keywords", []), card_id=cid)
            self.enemy.cards.append(card); self.card_sprite_list.append(card)
            slot = random.choice(free); slot.add_card(card); self.enemy.energy -= info.get("cost", 1)
            play_game_sound("enemy_place"); self.vfx.place(slot.center_x, slot.center_y, enemy=True); return True
        return False

    def start_fight(self):
        self.phase, self.phase_timer, self.fight_col = "fight", 0.0, 2
        play_game_sound("fight_start"); self.vfx.show_banner("БОЙ!", (255, 40, 40), 1.6, style="fight"); self.vfx.shake(5)

    def _apply_attack(self, attacker, defender, dmg, atk_player, def_player):
        if defender:
            dealt = defender.take_hit(dmg, source=attacker)
            if attacker.has_kw("lifesteal"): atk_player.heal(dealt)
            if attacker.has_kw("fire"):
                for o in def_player.cards:
                    if o != defender and o.hp > 0: o.take_hit(1)
            if attacker.has_kw("execute") and 0 < defender.hp <= 1: defender.hp = 0
            self.vfx.float_text(defender.center_x, defender.center_y + 20 * self.lay.s, f"-{dmg}", (255, 70, 70))
            self.vfx.kick(defender, +1)
        else:
            def_player.take_damage(dmg)
            if attacker.has_kw("lifesteal"): atk_player.heal(dmg)
            if attacker.has_kw("fire"):
                for o in def_player.cards:
                    if o.hp > 0: o.take_hit(1)
            self.vfx.hero_hit("enemy" if def_player == self.enemy else "player", dmg)
            self.vfx.kick(attacker, +1, 22)
        if defender and defender.hp <= 0 and self._handle_death(defender): self.vfx.card_death(defender)

    def resolve_column(self, col):
        p, e = self._card_at(col, 1), self._card_at(col, 3)
        if not p and not e: return
        self.vfx.column_glow(col)
        p_dmg = (0 if p.frozen_turns else p.strength) * (2 if p.has_kw("double_strike") else 1) if p else 0
        e_dmg = (0 if e.frozen_turns else e.strength) * (2 if e.has_kw("double_strike") else 1) if e else 0
        if p_dmg > 0 and p.stealth: p.stealth, p.alpha = False, 255
        if e_dmg > 0 and e.stealth: e.stealth, e.alpha = False, 255
        p_can_hit = not (p and e and e.has_kw("flying") and not p.has_kw("flying"))
        e_can_hit = not (p and e and p.has_kw("flying") and not e.has_kw("flying"))
        
        if p and p_can_hit and p_dmg > 0: self._apply_attack(p, e, p_dmg, self.player, self.enemy)
        if e and e_can_hit and e_dmg > 0: self._apply_attack(e, p, e_dmg, self.enemy, self.player)
        
        if p and e and p_dmg > 0 and e_dmg > 0 and p_can_hit and e_can_hit:
            play_game_sound("hit"); self.vfx.clash(p, e, p_dmg, e_dmg)
        elif (p and p_can_hit and p_dmg > 0) or (e and e_can_hit and e_dmg > 0):
            play_game_sound("hero_hit") if not (p and e) else None
            
        self._check_game_over()

    def start_player_turn(self):
        self.phase, self.phase_timer = "player", 0.0
        self.player.energy, self.player.ability_used = self.player.max_energy, False
        self.pending_util, self._targeting_util = None, False
        self.player.immune_turns = max(0, self.player.immune_turns - 1)
        for card in self.card_sprite_list:
            if card.frozen_turns > 0: card.frozen_turns -= 1
            if card.tick_poison() and self._handle_death(card): self.vfx.card_death(card)
        for card in self.player.cards:
            if card.has_kw("regen") and card.hp > 0: card.hp = min(card.max_hp, card.hp + 1)
            if card.has_kw("magic") and self.enemy.cards:
                target = random.choice(self.enemy.cards); target.take_hit(1)
                if target.hp <= 0 and self._handle_death(target): self.vfx.card_death(target)
        if len(self.player.hand) < MAX_HAND:
            if cid := self.player.draw_card_id(): self._spawn_player_card(cid)
        self._check_game_over()
        if self.phase == "over": return
        play_game_sound("turn_start"); self.vfx.show_banner("ВАШ ХОД", (255, 210, 80), 1.2); self.vfx.energy_refill()

    def _use_hero_ability(self):
        if self.phase != "player" or self.player.ability_used or not self.player.ability_name: return
        self.player.ability_used = True; self.vfx.shake(3); play_game_sound("ability")
        L = self.lay
        if self.hero_id == "knight": self.player.heal(3); self.vfx.float_text(*L.player_hero, "+3", (120, 255, 120), size=32); play_game_sound("heal")
        elif self.hero_id == "beastmaster" and self.player.cards:
            target = random.choice(self.player.cards); target.strength += 2
            self.vfx.float_text(target.center_x, target.center_y + 20 * L.s, "+2", (255, 200, 80), size=32); play_game_sound("buff")
        elif self.hero_id == "necromancer":
            self.player.hp = max(0, self.player.hp - 2); self.vfx.float_text(*L.player_hero, "-2", (255, 80, 80), size=24); play_game_sound("debuff")
            if self.enemy.cards:
                target = random.choice(self.enemy.cards); target.take_hit(4)
                self.vfx.float_text(target.center_x, target.center_y + 20 * L.s, "-4", (255, 80, 80), size=32)
                if target.hp <= 0 and self._handle_death(target): self.vfx.card_death(target)
        elif self.hero_id == "trickster":
            enemies = [c for c in self.enemy.cards if c.frozen_turns <= 0]
            if enemies:
                target = random.choice(enemies); target.frozen_turns = 1
                self.vfx.float_text(target.center_x, target.center_y + 20 * L.s, "ЗАМОРОЗКА", (100, 200, 255), size=22); play_game_sound("debuff")
        self._check_game_over()

    def _select_utility(self, idx):
        if idx >= len(self.player_utilities) or not (util := self.player_utilities[idx]): return
        if self.pending_util is util and self.pending_util_idx == idx: self._apply_selected_util(); return
        if self.pending_util: self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False
        if self.player.energy < util.get("cost", 0): play_game_sound("error"); return
        self.pending_util, self.pending_util_idx = util, idx; play_game_sound("card_select")

    def _apply_selected_util(self):
        util, idx = self.pending_util, self.pending_util_idx
        if not util: return
        if not (target_type := UTIL_TARGETS.get(util["id"])):
            if use_utility(self, util["id"], None):
                self.player.energy -= util.get("cost", 0)
                if idx is not None: self.player_utilities[idx] = None
            self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False
        else:
            if (target_type == "enemy_card" and not self.enemy.cards) or (target_type == "ally_card" and not self.player.cards): play_game_sound("error"); return
            self._targeting_util = True; play_game_sound("card_select")

    def _try_apply_pending_util(self, x, y):
        util = self.pending_util
        if not util: return
        target_type, target = UTIL_TARGETS.get(util["id"]), None
        if target_type in ("enemy_card", "ally_card"):
            for c in arcade.get_sprites_at_point((x, y), self.card_sprite_list):
                if target_type == "enemy_card" and c.player == self.enemy and not c.stealth: target = c; break
                if target_type == "ally_card" and c.player == self.player: target = c; break
            if not target: self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False; return
        if use_utility(self, util["id"], target):
            self.player.energy -= util.get("cost", 0)
            if self.pending_util_idx is not None: self.player_utilities[self.pending_util_idx] = None
        self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False
        self._check_game_over()

    def _shake_begin(self):
        if not self._shake_cam or not settings.get("screen_shake"): return False
        dx, dy = self.vfx.shake_offset()
        if dx == 0 and dy == 0: return False
        try: self._shake_cam.match_window(); self._shake_cam.position = (self.window.width / 2 + dx, self.window.height / 2 + dy); self._shake_cam.use(); return True
        except Exception: self._shake_cam = None; return False

    def on_show_view(self):
        try: self.window.set_exclusive_mouse(False)
        except Exception: pass

    def on_draw(self):
        self.clear()
        L, shaking = self.lay, self._shake_begin()
        if self.bg_texture:
            scale_bg = max(L.w / self.bg_texture.width, L.h / self.bg_texture.height)
            bg_w, bg_h = self.bg_texture.width * scale_bg, self.bg_texture.height * scale_bg
            arcade.draw_texture_rect(self.bg_texture, arcade.LBWH((L.w - bg_w) / 2, (L.h - bg_h) / 2, bg_w, bg_h))
        
        self.grid.update()
        for slot in self.slot_sprite_list: slot.draw()
        self.vfx.draw_under()
        draw_ui(self)
        self.card_sprite_list.draw(filter=gl.NEAREST)
        for card in self.card_sprite_list: card.draw_highlight()
        self.vfx.draw_world()
        self.vfx.draw_overlay()
        if shaking: self.window.default_camera.use()

    def on_update(self, delta_time):
        self.time += delta_time
        self.vfx.update(delta_time * max(0.1, settings.get("animation_speed")))
        for card, anim in list(self._card_anims.items()):
            anim[4] += delta_time; k = min(1.0, anim[4] / anim[5]); eased = 1 - (1 - k) ** 3
            card.center_x, card.center_y = anim[0] + (anim[2] - anim[0]) * eased, anim[1] + (anim[3] - anim[1]) * eased
            if k >= 1.0: card.center_x, card.center_y, card._animating = anim[2], anim[3], False; del self._card_anims[card]
        if not self._intro_done:
            self._intro_done = True
            self.vfx.show_banner(f"НОЧЬ {self.night}", (200, 90, 230), 1.5); self.vfx.show_banner("ВАШ ХОД", (255, 210, 80), 1.2)
        if self.phase == "enemy":
            self.phase_timer += delta_time
            if self.phase_timer >= 0.8:
                self.phase_timer = 0.0
                if not self.enemy_take_action(): self.start_fight()
        elif self.phase == "fight":
            self.phase_timer += delta_time
            if self.phase_timer >= 0.7:
                self.phase_timer = 0.0; self.resolve_column(self.fight_col)
                if self.phase == "over": return
                self.fight_col += 1
                if self.fight_col > 7: self.start_player_turn()
        if self.dialog_dur > 0: self.dialog_age += delta_time

    def on_key_press(self, key, modifiers):
        if self.phase == "over":
            if key == arcade.key.ESCAPE:
                from MainMenu import MainMenu; self.window.show_view(MainMenu())
            elif key in _CONFIRM_KEYS: self._handle_game_over_click()
            return
        if key == arcade.key.ESCAPE:
            if self.pending_util: self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False; return
            play_sfx(load_ui_sounds()[1])
            from PauseMenu import PauseMenu; self.window.show_view(PauseMenu(self))

    def _toggle_active(self, card):
        was_active = self.player.active == card
        if self.player.active: self.player.active.deselect(); self.player.active = None
        if not was_active: self.player.active = card; card.select(); self.vfx.select(card.center_x, card.center_y)
        play_game_sound("card_deselect" if was_active else "card_select")
        return not was_active

    def on_mouse_motion(self, x, y, dx, dy):
        self._hovered_card = self._hovered_util_idx = None
        if self.phase != "player": return
        hits = arcade.get_sprites_at_point((x, y), self.hand_sprite_list)
        if hits: self._hovered_card = hits[0]
        else:
            hits = arcade.get_sprites_at_point((x, y), self.card_sprite_list)
            if hits: self._hovered_card = hits[0]
        for i, (ux, uy, uw, uh) in enumerate(self._util_rects):
            if ux <= x <= ux + uw and uy <= y <= uy + uh: self._hovered_util_idx = i; break

    def on_mouse_press(self, x, y, button, modifiers):
        if self.phase == "over":
            if button == arcade.MOUSE_BUTTON_LEFT: self._handle_game_over_click()
            return
        if button == arcade.MOUSE_BUTTON_RIGHT:
            if self.pending_util: self.pending_util, self.pending_util_idx, self._targeting_util = None, None, False; play_game_sound("card_deselect")
            return
        if button != arcade.MOUSE_BUTTON_LEFT or self.phase != "player": return
        if self.pending_util and self._targeting_util: self._try_apply_pending_util(x, y); return
        if self._ability_btn_rect:
            bx, by, bw, bh = self._ability_btn_rect
            if bx <= x <= bx + bw and by <= y <= by + bh: self._use_hero_ability(); return
        for i, (ux, uy, uw, uh) in enumerate(self._util_rects):
            if ux <= x <= ux + uw and uy <= y <= uy + uh: self._select_utility(i); return
        L = self.lay
        if L.btn_x <= x <= L.btn_x + L.btn_w and L.btn_y <= y <= L.btn_y + L.btn_h:
            play_game_sound("end_turn"); self._maybe_tutorial("end_turn"); self.start_enemy_turn(); return
        hit_hand = arcade.get_sprites_at_point((x, y), self.hand_sprite_list)
        if hit_hand: self._toggle_active(hit_hand[0]); return
        hit_board = arcade.get_sprites_at_point((x, y), self.card_sprite_list)
        if hit_board: self._toggle_active(hit_board[0]); return
        hit_slots = arcade.get_sprites_at_point((x, y), self.slot_sprite_list)
        if hit_slots:
            slot, card = hit_slots[0], self.player.active
            if not (card and card in self.player.hand): return
            if slot.grid_y != 1 or slot.card is not None: play_game_sound("error"); return
            if self.player.energy < (info := self.cards_by_id.get(card.texture_name, {})).get("cost", 1): play_game_sound("error"); return
            old_x, old_y = card.center_x, card.center_y
            self.player.hand.remove(card); self.hand_sprite_list.remove(card); self.player.cards.append(card); self.card_sprite_list.append(card)
            slot.add_card(card); card.center_x, card.center_y = old_x, old_y; card._animating = True
            self._card_anims[card] = [old_x, old_y, slot.center_x, slot.center_y, 0.0, 0.25]
            card.deselect(); self.player.active = None; self.player.energy -= info.get("cost", 1)
            play_game_sound("card_place"); self.vfx.place(slot.center_x, slot.center_y); self.vfx.energy_spark(self.player.energy / self.player.max_energy)
            self._maybe_tutorial("cards")
            if card.has_kw("sacrifice"): self.player.take_damage(2); self.vfx.hero_hit("player", 2)
            if card.has_kw("heal"): self.player.heal(2)
            if card.has_kw("draw") and len(self.player.hand) < MAX_HAND:
                if cid := self.player.draw_card_id(): self._spawn_player_card(cid)
            if card.has_kw("buff"):
                allies = [c for c in self.player.cards if c != card]
                if allies: random.choice(allies).strength += 1