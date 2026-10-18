import arcade
from arcade import gl

from utils import FONT_TITLE


class Card(arcade.Sprite):
	def __init__(self, view, player, hp, strength, texture_name):
		super().__init__('images/cards/' + texture_name + '.png')
		self.texture_name = texture_name
		self.view = view
		self.player = player
		self.hp = hp
		self.strength = strength
		self.slot = None

		self.scale = 6.5

		self.view.card_sprite_list.append(self)

		self.heart = arcade.Sprite('images/cards/heart.png')
		self.heart.scale = self.scale[0] / 2
		self.view.heart_sprite_list.append(self.heart)

		self.sword = arcade.Sprite('images/cards/sword.png')
		self.sword.scale = self.scale[0] / 2
		self.view.sword_sprite_list.append(self.sword)

		self.hp_text = arcade.Text(
			text=str(self.hp), x=0, y=0,
			color=arcade.color.Color.from_hex_string('89000f'),
			font_size=25, font_name=FONT_TITLE
		)

		self.sword_text = arcade.Text(
			text=str(self.strength), x=0, y=0,
			color=arcade.color.Color.from_hex_string('848484'),
			font_size=25, font_name=FONT_TITLE
		)

	def on_draw(self, x):
		#self.center_x = self.view.window.width / 2 + ((len(self.player.cards) - 1) / 2 - x) * 150
		#self.center_y = self.view.window.height / 2 + (y - 0.5) * 170
		self.heart.center_x = self.center_x + self.scale[0] * 4.25
		self.heart.center_y = self.center_y + self.scale[0] * 8.25
		self.sword.center_x = self.center_x - self.scale[0] * 4.25
		self.sword.center_y = self.center_y - self.scale[0] * 8.25

		if len(str(self.hp)) == 1:
			self.hp_text.x = self.center_x + self.scale[0] * 1.25
		else:
			self.hp_text.x = self.center_x + self.scale[0] * 0.25
		self.hp_text.y = self.center_y + self.scale[0] * 6.5

		self.sword_text.x = self.center_x - self.scale[0] * 2
		self.sword_text.y = self.center_y - self.scale[0] * 10

	def draw(self):
		self.hp_text.draw()
		self.sword_text.draw()

	def select(self):
		self.texture = arcade.load_texture('images/cards/' + self.texture_name + '_select.png')
		self.scale = 7

	def deselect(self):
		self.texture = arcade.load_texture('images/cards/' + self.texture_name + '.png')
		self.scale = 6.5

	def deal_damage(self, from_card):
		self.hp -= from_card.strength
		self.hp = max(0, self.hp)

		self.hp_text.text = str(self.hp)

		if self.hp <= 0:
			self.player.remove_card(self)
			self.slot.remove_card()
			self.view.heart_sprite_list.remove(self.heart)
			self.view.sword_sprite_list.remove(self.sword)
			self.view.card_sprite_list.remove(self)
