class Grid:
    def __init__(self, view, w, h):
        self.view = view
        self.w = w
        self.h = h
        self.slots = dict()

    def add_slot(self, x, y, slot):
        self.slots[(x, y)] = slot
        slot.grid_x = x
        slot.grid_y = y
        self._update_slot(slot)

    def _update_slot(self, slot):
        w, h = self.view.window.width, self.view.window.height
        
        # Слоты по центру стола (от 20% до 80% ширины)
        start_x = w * 0.20
        end_x = w * 0.80
        total_slots = 6
        step_x = (end_x - start_x) / (total_slots - 1)
        
        slot.center_x = start_x + (slot.grid_x - 2) * step_x
        
        if slot.grid_y == 1:
            slot.center_y = h * 0.32 
        else:
            slot.center_y = h * 0.68 
        
        if slot.card:
            slot.card.center_x = slot.center_x
            slot.card.center_y = slot.center_y

    def add_card(self, x, y, card):
        self.slots[(x, y)].add_card(card)
        self._update_slot(self.slots[(x, y)])

    def update(self):
        for slot in self.slots.values():
            self._update_slot(slot)