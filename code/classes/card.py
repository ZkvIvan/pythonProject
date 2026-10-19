import arcade
from paths import asset

class Card(arcade.Sprite):
    def __init__(self, view, player, hp, strength, texture_name, description=""):
        super().__init__(asset("images", "Cards", f"{texture_name}.png"))
        self.texture_name = texture_name
        self.view = view
        self.player = player
        self.hp = hp
        self.strength = strength
        self.description = description
        self.slot = None
        self.is_selected = False
        
        self.base_scale = 1.0 
        self.scale = self.base_scale

    def select(self):
        self.scale = 1.1 
        self.is_selected = True

    def deselect(self):
        self.scale = self.base_scale
        self.is_selected = False

    def draw_highlight(self):
        if self.is_selected:
            import math
            w = self.width
            h = self.height
            inset = 0 
            
            left = self.center_x - w / 2 + inset
            bottom = self.center_y - h / 2 + inset
            width = w - (inset * 2)
            height = h - (inset * 2)
            
            pulse_alpha = 150 + int(math.sin(self.view.time * 5) * 105)
            color = (255, 50, 50, pulse_alpha)
            
            arcade.draw_lbwh_rectangle_outline(
                left, bottom, width, height, color, 10 
            )

    def deal_damage(self, from_card):
        self.hp -= from_card.strength
        self.hp = max(0, self.hp)

        if self.hp <= 0:
            self.player.remove_card(self)
            if self.slot:
                self.slot.remove_card()