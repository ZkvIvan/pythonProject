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
        # Позиции берём из единого лэйаута GameView (view.lay)
        L = self.view.lay

        slot.center_x = L.slot_x0 + (slot.grid_x - 2) * L.slot_step
        slot.center_y = L.enemy_row_y if slot.grid_y == 3 else L.player_row_y

        # Хитбокс слота должен совпадать с нарисованным (120s x 170s)
        if getattr(slot, "_applied_s", None) != L.s:
            slot.scale = L.s
            slot._applied_s = L.s

        if slot.card:
            slot.card.center_x = slot.center_x
            slot.card.center_y = slot.center_y

    def add_card(self, x, y, card):
        self.slots[(x, y)].add_card(card)
        self._update_slot(self.slots[(x, y)])

    def update(self):
        for slot in self.slots.values():
            self._update_slot(slot)