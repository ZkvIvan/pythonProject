class Grid:
	def __init__(self, view, w, h):
		self.view = view
		self.w = w
		self.h = h
		self.slots = dict()

	def add_slot(self, x, y, slot):
		self.slots[(x, y)] = slot
		slot.x = x
		slot.y = y

	def add_card(self, x, y, card):
		self.slots[(x, y)].add_card(card)

	def on_draw(self):
		for key in self.slots:
			self.slots[key].center_x = self.view.window.width / self.w * key[0]
			self.slots[key].center_y = self.view.window.height / self.h * key[1]

			self.slots[key].on_draw()
