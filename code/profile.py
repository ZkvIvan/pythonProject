import json
import random
from paths import data

PROFILE_PATH = data("profile.json")

class Profile:
    def __init__(self):
        self.hero_id, self.player_name, self.night = "knight", "Жнец", 1
        self.money, self.xp, self.level = 0, 0, 1
        self.owned_cards, self.deck, self.owned_utils, self.utils = [], [], [], []
        self.last_rewards = None

    @classmethod
    def new_game(cls, hero_id, player_name, deck_ids, util_ids):
        p = cls()
        p.hero_id, p.player_name = hero_id, player_name
        p.owned_cards, p.deck = list(deck_ids), list(deck_ids[:6])
        p.owned_utils, p.utils = list(util_ids), list(util_ids[:3])
        p.money = 50
        return p

    @property
    def max_hp(self): return 100 + (self.level - 1) * 10

    @property
    def max_energy(self): return 3 + (self.level - 1) // 2

    def xp_to_next(self): return 100 + (self.level - 1) * 40

    def add_xp(self, amount):
        self.xp += amount
        leveled = False
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level += 1
            leveled = True
        return leveled

    def add_money(self, amount): self.money = max(0, self.money + amount)

    def add_card(self, card_id):
        if card_id not in self.owned_cards: self.owned_cards.append(card_id)

    def add_util(self, util_id):
        if util_id not in self.owned_utils: self.owned_utils.append(util_id)

    def save(self):
        try:
            with open(PROFILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self.__dict__, f, indent=2, ensure_ascii=False)
        except Exception as e: print(f"[profile] save error: {e}")

    @classmethod
    def load(cls):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f: d = json.load(f)
            p = cls()
            for k, v in d.items():
                if hasattr(p, k): setattr(p, k, v)
            return p
        except Exception: return None

def starter_utils(count=3):
    try:
        with open(data("utilities.json"), "r", encoding="utf-8") as f: utils = json.load(f)
        return [u["id"] for u in random.sample(utils, min(count, len(utils)))]
    except Exception: return []