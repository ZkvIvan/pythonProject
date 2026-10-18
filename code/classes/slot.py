import arcade


class Slot(arcade.Sprite):
	def __init__(self, view):
		super().__init__('images/cards/slot.png')
		self.view = view
		self.card = None
		self.view.slot_sprite_list.append(self)
		self.scale = 6.5
		self.x = None
		self.y = None

	def add_card(self, card):
		self.card = card
		card.slot = self
		card.center_x = self.center_x
		card.center_y = self.center_y

	def remove_card(self):
		self.card = None

	def on_draw(self):
		#self.center_x = self.view.window.width / 2 + ((len(self.view.slot_sprite_list) / 2 - 1) / 2 - self.x) * 120
		#self.center_y = self.view.window.height / 2 + (self.y - 0.5) * 170
		if self.card:
			self.card.center_x = self.center_x
			self.card.center_y = self.center_y
