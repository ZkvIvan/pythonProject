import random

import arcade
from classes.card import Card

from utils import FONT_TITLE


class Player:
	def __init__(self, view, is_enemy=False):
		self.view = view
		self.cards = []
		self.active = None
		self.moves = 3
		self.hp = 30
		self.is_enemy = is_enemy

		self.hp_text = arcade.Text(
			text=str(self.hp), x=0, y=0,
			color=arcade.color.Color.from_hex_string('89000f'),
			font_size=40, font_name=FONT_TITLE
		)

	def can_move(self):
		return self.moves > 0

	def on_draw(self):
		if self.is_enemy:
			self.hp_text.y = self.view.window.height - 100
		else:
			self.hp_text.y = 100
		self.hp_text.x = self.view.window.width - 100
		for ix, card in enumerate(self.cards):
			card.on_draw(ix)

	def draw(self):
		self.hp_text.draw()
		for card in self.cards:
			card.draw()

	def remove_card(self, card):
		if self.active == card:
			self.active = None
		self.cards.remove(card)

	def turn_end(self):
		self.moves = 3

	def select_best(self):
		try:
			if not self.cards:
				self.active = None
				return

			for card in self.cards:
				if card.slot.y != 2:
					self.active = card
					break
			else:
				self.active = None

			for card in self.cards:
				if card.strength > self.active.strength and card.slot.y != 2:
					self.active = card
		except:
			self.active = None

	def get_most_dangerous(self):
		try:
			for card in self.cards:
				if card.slot.y == 2:
					res = card
					break
			else:
				return None

			for card in self.cards:
				if card.strength * card.hp > res.strength * res.hp and card.slot.y == 2:
					res = card

			return res
		except:
			return None

	def deal_damage(self, from_card):
		self.hp -= from_card.strength
		self.hp = max(0, self.hp)

		self.hp_text.text = str(self.hp)

		#if self.hp <= 0:
		#	self.player.remove_card(self)
		#	self.slot.remove_card()
		#	self.view.heart_sprite_list.remove(self.heart)
		#	self.view.sword_sprite_list.remove(self.sword)
		#	self.view.card_sprite_list.remove(self)
