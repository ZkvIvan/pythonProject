import random

class Player:
    def __init__(self, view, hero_id=None):
        self.view, self.hero_id = view, hero_id
        self.cards, self.hand, self.deck, self.discard = [], [], [], []
        self.active, self.moves = None, 3
        self.max_hp, self.hp = 100, 100
        self.max_energy, self.energy, self.level = 3, 3, 1
        self.immune_turns = 0
        self.ability_name, self.ability_text, self.ability_used = "", "", False

    def init_deck(self, card_ids):
        self.deck = list(card_ids)
        random.shuffle(self.deck)
        self.discard = []

    def draw_card_id(self):
        if not self.deck:
            if not self.discard: return None
            self.deck = list(self.discard)
            self.discard = []
            random.shuffle(self.deck)
        return self.deck.pop(0) if self.deck else None

    def heal(self, amount): self.hp = min(self.max_hp, self.hp + amount)
    
    def take_damage(self, amount):
        if self.immune_turns > 0: return 0
        self.hp = max(0, self.hp - amount)
        return amount

    def can_move(self): return self.moves > 0

    def remove_card(self, card):
        if self.active == card: self.active = None
        if card in self.cards: self.cards.remove(card)

    def turn_end(self): self.moves = 3