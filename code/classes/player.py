import random

from classes.card import Card


class Player:
	def __init__(self, view):
		self.view = view
		self.cards = []
		self.active = None
		self.moves = 3

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
