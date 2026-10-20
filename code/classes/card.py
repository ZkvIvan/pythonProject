import math
import arcade
from paths import asset

class Card(arcade.Sprite):
    def __init__(self, view, player, hp, strength, texture_name, description="", keywords=None, card_id=None):
        super().__init__(asset("images", "Cards", f"{texture_name}.png"))
        self.texture_name, self.card_id = texture_name, card_id or texture_name
        self.view, self.player = view, player
        self.max_hp, self.hp, self.strength = hp, hp, strength
        self.description, self.keywords = description, list(keywords or [])
        self.slot, self.is_selected, self.has_rebirthed = None, False, False
        self.poison_turns, self.frozen_turns, self.damage_taken_bonus = 0, 0, 0
        self.stealth = self.has_kw("stealth")
        self.alpha = 128 if self.stealth else 255
        self.fx_x, self.fx_y = 0.0, 0.0
        self.base_scale, self.scale = 1.0, 1.0

    def has_kw(self, kw):
        return kw in self.keywords

    def select(self): self.is_selected = True
    def deselect(self): self.is_selected = False

    def draw_highlight(self):
        if not self.is_selected: return
        w, h = self.width, self.height
        left, bottom = self.center_x - w / 2, self.center_y - h / 2
        pulse = 150 + int(math.sin(self.view.time * 5) * 105)
        arcade.draw_lbwh_rectangle_outline(left, bottom, w, h, (255, 50, 50, pulse), 10)

    def take_hit(self, amount, source=None):
        dmg = amount + self.damage_taken_bonus
        if self.has_kw("shield"): dmg = max(0, dmg - 2)
        self.hp -= dmg
        if self.has_kw("frenzy") and self.hp > 0: self.strength += 1
        if source:
            if source.has_kw("poison"): self.poison_turns = max(self.poison_turns, 2)
            if source.has_kw("stun") or source.has_kw("petrify"): self.frozen_turns = max(self.frozen_turns, 1)
            if source.has_kw("curse"): self.damage_taken_bonus += 1
        if self.stealth: self.stealth, self.alpha = False, 255
        self.hp = max(0, self.hp)
        return dmg

    def tick_poison(self):
        if self.poison_turns > 0 and self.hp > 0:
            self.hp = max(0, self.hp - 1)
            self.poison_turns -= 1
            return self.hp <= 0
        return False