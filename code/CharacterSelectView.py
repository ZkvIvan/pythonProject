import arcade
import arcade.gui
import json
from paths import data
from utils import FONT_TITLE, FONT_UI

class CharacterSelectView(arcade.View):
    def __init__(self):
        super().__init__()
        self.manager = arcade.gui.UIManager()
        self.name_input = arcade.gui.UIInputText(width=300, height=40, text="Жнец", font_size=16, font_name=FONT_UI)
        
        try:
            with open(data("characters.json"), "r", encoding="utf-8") as f:
                self.heroes = json.load(f)
        except:
            self.heroes = []
            
        self.hover_hero = None

    def on_show_view(self):
        self.manager.enable()
        anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        anchor.add(child=self.name_input, anchor_x="center_x", anchor_y="center_y", align_y=-150)

    def on_hide_view(self):
        self.manager.disable()

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        s = h / 1080
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (10, 10, 15))
        arcade.draw_text("ВЫБЕРИТЕ СУДЬБУ", w/2, h - 100*s, arcade.color.RED, 40*s, font_name=FONT_TITLE, anchor_x="center")
        arcade.draw_text("Введите имя:", w/2, h/2 - 100*s, arcade.color.WHITE, 20*s, font_name=FONT_UI, anchor_x="center")
        
        start_x = w/2 - 450*s
        for i, hero in enumerate(self.heroes):
            cx = start_x + i * 300*s
            cy = h/2 + 50*s
            rect = arcade.LBWH(cx - 120*s, cy - 150*s, 240*s, 300*s)
            
            is_hover = (i == self.hover_hero)
            bg_color = (40, 20, 20) if is_hover else (20, 20, 25)
            border = arcade.color.RED if is_hover else (100, 100, 100)
            
            arcade.draw_lbwh_rectangle_filled(rect.left, rect.bottom, rect.width, rect.height, bg_color)
            arcade.draw_lbwh_rectangle_outline(rect.left, rect.bottom, rect.width, rect.height, border, 3)
            arcade.draw_text(hero["name"], cx, cy + 100*s, arcade.color.WHITE, 22*s, font_name=FONT_UI, anchor_x="center")
            arcade.draw_text(f"{hero['ability_name']}\n{hero['ability_text']}", cx, cy - 30*s, arcade.color.LIGHT_GRAY, 14*s, font_name=FONT_UI, anchor_x="center", align="center", width=200*s)
        self.manager.draw()

    def on_mouse_motion(self, x, y, dx, dy):
        w, h = self.window.width, self.window.height
        s = h / 1080
        start_x = w/2 - 450*s
        self.hover_hero = None
        for i in range(len(self.heroes)):
            cx = start_x + i * 300*s
            cy = h/2 + 50*s
            if (cx - 120*s <= x <= cx + 120*s) and (cy - 150*s <= y <= cy + 150*s):
                self.hover_hero = i

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT: return
        w, h = self.window.width, self.window.height
        s = h / 1080
        start_x = w/2 - 450*s
        
        for i, hero in enumerate(self.heroes):
            cx = start_x + i * 300*s
            cy = h/2 + 50*s
            if (cx - 120*s <= x <= cx + 120*s) and (cy - 150*s <= y <= cy + 150*s):
                p_name = self.name_input.text.strip() or "Жнец"
                from GameView import GameView
                self.window.show_view(GameView(hero_id=hero["id"], player_name=p_name))