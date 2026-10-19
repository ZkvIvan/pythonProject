import random

from classes.card import Card


class Player:
	def __init__(self, view):
		self.view = view
		self.cards = []      # Карты на столе
		self.hand = []       # Карты в руке
		self.active = None
		self.moves = 3
        
        # Статы для HUD
		self.max_hp = 100
		self.hp = 85      
		self.max_energy = 3
		self.energy = 3
		self.level = 1

	def can_move(self):
		return self.moves > 0

	def on_draw(self):
		for ix, card in enumerate(self.cards):
			card.on_draw(ix)

	def draw(self):
		for card in self.cards:
			card.draw()

	def remove_card(self, card):
		if self.active == card:
			self.active = None
		self.cards.remove(card)

	def turn_end(self):
		self.moves = 3
