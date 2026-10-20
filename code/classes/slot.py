import arcade


class Slot(arcade.Sprite):
    def __init__(self, view):
        empty_texture = arcade.Texture.create_empty("empty_slot", (120, 170))
        super().__init__(empty_texture)
        self.view = view
        self.card = None
        self.view.slot_sprite_list.append(self)
        self.scale = 1.0
        self.grid_x = 0
        self.grid_y = 0

    def add_card(self, card):
        self.card = card
        card.slot = self
        card.center_x = self.center_x
        card.center_y = self.center_y

    def remove_card(self):
        self.card = None

    def draw(self):
        if self.card:
            return
        s = self.view.window.height / 1080
        w, h = 120 * s, 170 * s
        left = self.center_x - w / 2
        bottom = self.center_y - h / 2
        # почти чёрная подложка
        arcade.draw_lbwh_rectangle_filled(left, bottom, w, h, (5, 5, 8, 140))
        arcade.draw_lbwh_rectangle_outline(left, bottom, w, h, (50, 50, 60), 2)
        # центральная точка вместо крестика
        arcade.draw_circle_filled(self.center_x, self.center_y,
                                  2.5 * s, (70, 70, 80))