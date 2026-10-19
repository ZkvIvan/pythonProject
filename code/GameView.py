import math
import json
import arcade
from arcade import gl

from paths import data, asset
from classes.player import Player
from classes.slot import Slot
from classes.card import Card
from classes.grid import Grid

class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        self.time = 0.0
        self.is_player_turn = True
        self.turn_timer = 0.0
        
        self.info_panel_x = self.window.width

        self.card_sprite_list = arcade.SpriteList()
        self.slot_sprite_list = arcade.SpriteList()
        self.hand_sprite_list = arcade.SpriteList()
        self.discard_pile = []

        self.player = Player(self)
        self.enemy = Player(self)
        self.enemy.hp = 45 

        self.icon_hp = arcade.load_texture(asset("images", "icons", "hp_icon.png"))
        self.icon_dmg = arcade.load_texture(asset("images", "icons", "damage_icon.png"))
        
        try:
            self.bg_texture = arcade.load_texture(asset("images", "background_table.png"))
            self.enemy_portrait = arcade.load_texture(asset("images", "enemy", "boss.png"))
        except:
            self.bg_texture = None
            self.enemy_portrait = None

        self.grid = Grid(self, 9, 4)
        for i in range(2, 8): 
            self.grid.add_slot(i, 1, Slot(self))
            self.grid.add_slot(i, 3, Slot(self))

        try:
            with open(data("cards.json"), "r", encoding="utf-8") as f:
                self.cards_data = json.load(f)
            with open(data("utilities.json"), "r", encoding="utf-8") as f:
                self.utilities_data = json.load(f)
        except Exception as e:
            self.cards_data = []
            self.utilities_data = []

        self._draw_initial_hand()

    def _draw_initial_hand(self):
        if not self.cards_data: return
        # ИСПРАВЛЕНО: Теперь 6 карт у игрока
        for i in range(6):
            info = self.cards_data[i]
            card = Card(self, self.player, hp=info["hp"], strength=info["attack"], texture_name=info["id"], description=info.get("text", ""))
            self.player.hand.append(card)
            self.hand_sprite_list.append(card) 

        # Врагу 2 карты на стол
        for i in range(2):
            info = self.cards_data[i + 6]
            card = Card(self, self.enemy, hp=info["hp"], strength=info["attack"], texture_name=info["id"])
            self.enemy.cards.append(card)
            self.card_sprite_list.append(card)
            self.grid.add_card(i + 4, 3, card)

    def draw_turn_indicator(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        cx, cy = w * 0.08, h * 0.5
        radius = 60 * s
        
        if self.is_player_turn:
            pulse = math.sin(self.time * 3)
            alpha = int(100 + (pulse * 50))
            arcade.draw_circle_filled(cx, cy, radius + (pulse * 10), (255, 200, 0, alpha))
            arcade.draw_circle_outline(cx, cy, radius, (255, 255, 255, 255), 4)
            arcade.draw_text("ВАШ\nХОД", cx, cy, arcade.color.WHITE, 22 * s, font_name="Cyrillic Pixel-7", align="center", anchor_x="center", anchor_y="center")
            
            btn_w, btn_h = 160 * s, 45 * s
            btn_x, btn_y = cx - (btn_w / 2), cy - radius - (60 * s)
            arcade.draw_lbwh_rectangle_filled(btn_x, btn_y, btn_w, btn_h, (60, 40, 20))
            arcade.draw_lbwh_rectangle_outline(btn_x, btn_y, btn_w, btn_h, (200, 150, 50), 2)
            arcade.draw_text("ЗАВЕРШИТЬ", cx, btn_y + btn_h/2, arcade.color.WHITE, 14 * s, font_name="Cyrillic Pixel-7", anchor_x="center", anchor_y="center")
        else:
            arcade.draw_circle_filled(cx, cy, radius, (50, 50, 50, 150))
            arcade.draw_circle_outline(cx, cy, radius, (100, 100, 100), 4)
            arcade.draw_text("ХОД\nВРАГА", cx, cy, arcade.color.LIGHT_GRAY, 18 * s, font_name="Cyrillic Pixel-7", align="center", anchor_x="center", anchor_y="center")
            
            btn_w, btn_h = 160 * s, 45 * s
            btn_x, btn_y = cx - (btn_w / 2), cy - radius - (60 * s)
            arcade.draw_lbwh_rectangle_filled(btn_x, btn_y, btn_w, btn_h, (30, 30, 30))
            arcade.draw_lbwh_rectangle_outline(btn_x, btn_y, btn_w, btn_h, (80, 80, 80), 2)
            arcade.draw_text("ОЖИДАНИЕ", cx, btn_y + btn_h/2, arcade.color.GRAY, 14 * s, font_name="Cyrillic Pixel-7", anchor_x="center", anchor_y="center")

    def draw_deck_and_discard(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        
        # КОЛОДА (Слева)
        deck_cx, deck_cy = w * 0.08, h * 0.5
        arcade.draw_lbwh_rectangle_filled(deck_cx - 50*s, deck_cy - 70*s, 100*s, 140*s, (20, 20, 30, 200))
        arcade.draw_lbwh_rectangle_outline(deck_cx - 50*s, deck_cy - 70*s, 100*s, 140*s, (80, 80, 120), 2)
        arcade.draw_text("КОЛОДА", deck_cx, deck_cy, arcade.color.DARK_GRAY, 18*s, font_name="Cyrillic Pixel-7", anchor_x="center", anchor_y="center")

        # СБРОС (Справа)
        disc_cx, disc_cy = w * 0.92, h * 0.5
        arcade.draw_lbwh_rectangle_filled(disc_cx - 50*s, disc_cy - 70*s, 100*s, 140*s, (30, 10, 10, 200))
        arcade.draw_lbwh_rectangle_outline(disc_cx - 50*s, disc_cy - 70*s, 100*s, 140*s, (120, 50, 50), 2)
        arcade.draw_text("СБРОС", disc_cx, disc_cy, arcade.color.DARK_GRAY, 18*s, font_name="Cyrillic Pixel-7", anchor_x="center", anchor_y="center")
        
        for i, card in enumerate(self.discard_pile):
            offset = i * 2 * s
            if offset > 20 * s: break
            arcade.draw_lbwh_rectangle_filled(disc_cx - 50*s + offset, disc_cy - 70*s + offset, 100*s, 140*s, (60, 30, 30, 150))

    def draw_enemy_hud(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        hud_h = 160 * s
        
        arcade.draw_lbwh_rectangle_filled(0, h - hud_h, w, hud_h, (15, 15, 20))
        arcade.draw_lbwh_rectangle_filled(0, h - hud_h, w, 2, (100, 100, 100))
        
        # 1. Статы врага (Слева: 0% - 25%)
        bar_x, bar_y = 30 * s, h - hud_h + 25 * s
        bar_w = 280 * s
        arcade.draw_text("ВРАГ", bar_x, bar_y + 60 * s, arcade.color.WHITE, 22 * s, font_name="Cyrillic Pixel-7")
        self._draw_bar(bar_x, bar_y + 30 * s, bar_w, 25 * s, self.enemy.hp, self.enemy.max_hp, arcade.color.RED)
        arcade.draw_text(f"HP: {self.enemy.hp}/{self.enemy.max_hp}", bar_x + 10 * s, bar_y + 35 * s, arcade.color.WHITE, 16 * s, font_name="Cyrillic Pixel-7")
        self._draw_bar(bar_x, bar_y - 5 * s, bar_w, 25 * s, self.enemy.energy, self.enemy.max_energy, arcade.color.CYAN)
        arcade.draw_text(f"EN: {self.enemy.energy}/{self.enemy.max_energy}", bar_x + 10 * s, bar_y, arcade.color.WHITE, 16 * s, font_name="Cyrillic Pixel-7")

        # 2. Портрет врага (Центр)
        if self.enemy_portrait:
            p_h = hud_h 
            p_w = p_h * (self.enemy_portrait.width / self.enemy_portrait.height)
            p_x = (w / 2) - (p_w / 2)
            p_y = h - p_h 
            
            # РАМКА КАК У ИГРОКА (Цвет от HP)
            hp_ratio = self.enemy.hp / self.enemy.max_hp
            frame_color = arcade.color.WHITE if hp_ratio > 0.6 else arcade.color.YELLOW_ORANGE if hp_ratio > 0.3 else arcade.color.DARK_RED
            
            arcade.draw_texture_rect(self.enemy_portrait, arcade.LBWH(p_x, p_y, p_w, p_h))
            arcade.draw_lbwh_rectangle_outline(p_x, p_y, p_w, p_h, frame_color, 4)

        # 3. Карты врага (Справа: 75% - 98%) - УВЕЛИЧЕНЫ
        card_start_x = w * 0.75
        card_w = (w * 0.23) / 6 
        for i in range(6):
            cx = card_start_x + (i * card_w)
            arcade.draw_lbwh_rectangle_filled(cx, h - hud_h + 25 * s, card_w - 5*s, 110 * s, (40, 20, 20))
            arcade.draw_lbwh_rectangle_outline(cx, h - hud_h + 25 * s, card_w - 5*s, 110 * s, (100, 50, 50), 2)

    def _draw_bar(self, x, y, width, height, current, max_val, color):
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (30, 30, 35))
        if current > 0:
            bar_width = width * (max(0, current) / max_val)
            arcade.draw_lbwh_rectangle_filled(x, y, bar_width, height, color)
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, (100, 100, 100), 2)

    def draw_player_hud(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        hud_h = 200 * s
        
        arcade.draw_lbwh_rectangle_filled(0, 0, w, hud_h, (15, 15, 20))
        arcade.draw_lbwh_rectangle_filled(0, hud_h, w, 2, (100, 100, 100))

        x_sep1 = w * 0.35
        x_sep2 = w * 0.55
        arcade.draw_lbwh_rectangle_filled(x_sep1, 0, 4, hud_h, (80, 80, 80))
        arcade.draw_lbwh_rectangle_filled(x_sep2, 0, 4, hud_h, (80, 80, 80))

        # 1. Статы игрока (0% - 35%)
        avatar_size = 130 * s
        avatar_x, avatar_y = 20 * s, 35 * s
        hp_ratio = self.player.hp / self.player.max_hp
        frame_color = arcade.color.WHITE if hp_ratio > 0.6 else arcade.color.YELLOW_ORANGE if hp_ratio > 0.3 else arcade.color.DARK_RED
        
        arcade.draw_lbwh_rectangle_filled(avatar_x, avatar_y, avatar_size, avatar_size, (30, 30, 35))
        arcade.draw_lbwh_rectangle_outline(avatar_x, avatar_y, avatar_size, avatar_size, frame_color, 4)
        arcade.draw_text("ГЕРОЙ", avatar_x, avatar_y + avatar_size + 5 * s, frame_color, 18 * s, font_name="Cyrillic Pixel-7")

        bar_x = avatar_x + avatar_size + 15 * s
        bar_w = 220 * s
        self._draw_bar(bar_x, avatar_y + 85 * s, bar_w, 25 * s, self.player.hp, self.player.max_hp, arcade.color.RED)
        arcade.draw_text(f"HP: {self.player.hp}/{self.player.max_hp}", bar_x + 10 * s, avatar_y + 90 * s, arcade.color.WHITE, 14 * s, font_name="Cyrillic Pixel-7")
        self._draw_bar(bar_x, avatar_y + 45 * s, bar_w, 25 * s, self.player.energy, self.player.max_energy, arcade.color.CYAN)
        arcade.draw_text(f"EN: {self.player.energy}/{self.player.max_energy}", bar_x + 10 * s, avatar_y + 50 * s, arcade.color.WHITE, 14 * s, font_name="Cyrillic Pixel-7")
        self._draw_bar(bar_x, avatar_y + 5 * s, bar_w, 25 * s, self.player.level, 10, arcade.color.GOLD)
        arcade.draw_text(f"LVL: {self.player.level}", bar_x + 10 * s, avatar_y + 10 * s, arcade.color.WHITE, 14 * s, font_name="Cyrillic Pixel-7")

        # 2. Утилиты (35% - 55%) - ЛЕВЕЕ РУКИ
        util_start_x = w * 0.37
        util_w = 90 * s
        util_h = 120 * s
        util_y = 45 * s 
        
        arcade.draw_text("УТИЛИТЫ", util_start_x, hud_h - 25 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name="Cyrillic Pixel-7")
        util_x = util_start_x
        for i in range(3):
            arcade.draw_lbwh_rectangle_filled(util_x, util_y, util_w, util_h, (30, 30, 35))
            arcade.draw_lbwh_rectangle_outline(util_x, util_y, util_w, util_h, (100, 100, 100), 2)
            if i < len(self.utilities_data):
                arcade.draw_text(self.utilities_data[i]["name"], util_x + 5 * s, util_y + util_h/2, arcade.color.WHITE, 12 * s, font_name="Cyrillic Pixel-7", width=util_w - 10*s, align="center", anchor_y="center")
            util_x += util_w + (10 * s)

        # 3. Рука (55% - 100%)
        arcade.draw_text("РУКА", w * 0.57, hud_h - 25 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name="Cyrillic Pixel-7")

    def draw_hand(self):
        w, h = self.window.width, self.window.height
        s = h / 1080
        
        zone_start_x = w * 0.57
        zone_end_x = w * 0.98
        zone_width = zone_end_x - zone_start_x
        
        # ИСПРАВЛЕНО: 6 слотов для 6 карт!
        num_slots = 6
        slot_spacing = zone_width / num_slots
        card_scale = 1.0 * s # Чуть уменьшили масштаб, чтобы 6 карт влезли
        card_w = 100 * card_scale
        card_h = 140 * card_scale
        
        start_x = zone_start_x + (slot_spacing / 2)
        cy = 90 * s 
        
        for i in range(num_slots):
            cx = start_x + (i * slot_spacing)
            left = cx - card_w / 2
            bottom = cy - card_h / 2
            arcade.draw_lbwh_rectangle_filled(left, bottom, card_w, card_h, (10, 10, 12, 150))
            arcade.draw_lbwh_rectangle_outline(left, bottom, card_w, card_h, (60, 60, 60), 2)
            arcade.draw_line(left + 30*s, bottom + 30*s, left + card_w - 30*s, bottom + card_h - 30*s, (50, 20, 20), 2)
            arcade.draw_line(left + card_w - 30*s, bottom + 30*s, left + 30*s, bottom + card_h - 30*s, (50, 20, 20), 2)

        for i, card in enumerate(self.player.hand):
            card.scale = card_scale
            card.center_x = start_x + (i * slot_spacing)
            card.center_y = cy 
            
        self.hand_sprite_list.draw(filter=gl.NEAREST)
        for card in self.player.hand:
            card.draw_highlight()

    def draw_card_info(self):
        if not self.player.active and self.info_panel_x >= self.window.width:
            return
            
        s = self.window.height / 1080
        card = self.player.active if self.player.active else None
        h = self.window.height
        
        # Увеличили панель, чтобы текст 100% влезал
        panel_w, panel_h = 350 * s, 450 * s
        panel_y = (h - panel_h) / 2 + 50 * s
        
        arcade.draw_lbwh_rectangle_filled(self.info_panel_x, panel_y, panel_w, panel_h, (15, 15, 20, 240))
        arcade.draw_lbwh_rectangle_outline(self.info_panel_x, panel_y, panel_w, panel_h, (100, 100, 100), 2)

        if card:
            arcade.draw_text(card.texture_name, self.info_panel_x + 15 * s, panel_y + panel_h - 40 * s, arcade.color.WHITE, 22 * s, font_name="Cyrillic Pixel-7")
            
            arcade.draw_texture_rect(self.icon_hp, arcade.LBWH(self.info_panel_x + 20 * s, panel_y + panel_h - 100 * s, 35 * s, 35 * s))
            arcade.draw_text(f"{card.hp}", self.info_panel_x + 65 * s, panel_y + panel_h - 95 * s, arcade.color.RED, 24 * s, font_name="Cyrillic Pixel-7")

            arcade.draw_texture_rect(self.icon_dmg, arcade.LBWH(self.info_panel_x + 150 * s, panel_y + panel_h - 100 * s, 35 * s, 35 * s))
            arcade.draw_text(f"{card.strength}", self.info_panel_x + 195 * s, panel_y + panel_h - 95 * s, arcade.color.GOLD, 24 * s, font_name="Cyrillic Pixel-7")

            arcade.draw_text(
                card.description, 
                self.info_panel_x + 15 * s, panel_y + panel_h - 170 * s, 
                arcade.color.LIGHT_GRAY, 16 * s, font_name="Cyrillic Pixel-7", 
                width=int(panel_w - 30 * s), 
                multiline=True
            )

    def on_draw(self):
        self.clear()
        
        if self.bg_texture:
            scale_w = self.window.width / self.bg_texture.width
            scale_h = self.window.height / self.bg_texture.height
            scale_bg = max(scale_w, scale_h)
            bg_w = self.bg_texture.width * scale_bg
            bg_h = self.bg_texture.height * scale_bg
            arcade.draw_texture_rect(self.bg_texture, arcade.LBWH((self.window.width - bg_w)/2, (self.window.height - bg_h)/2, bg_w, bg_h))
        
        self.draw_turn_indicator()
        self.draw_deck_and_discard()
        self.grid.update()
        for slot in self.slot_sprite_list:
            slot.draw()
            
        for card in self.card_sprite_list:
            card.draw_highlight()
        self.card_sprite_list.draw(filter=gl.NEAREST)

        self.draw_enemy_hud()
        self.draw_player_hud()
        self.draw_hand()
        self.draw_card_info()

    def on_update(self, delta_time):
        self.time += delta_time
        
        s = self.window.height / 1080
        panel_w = 350 * s
        target_x = self.window.width - panel_w - 20 * s if self.player.active else self.window.width
        self.info_panel_x += (target_x - self.info_panel_x) * 15 * delta_time

        if not self.is_player_turn:
            self.turn_timer += delta_time
            if self.turn_timer >= 2.0:
                self.is_player_turn = True
                self.turn_timer = 0.0
                self.player.energy = self.player.max_energy

    def on_mouse_press(self, x, y, button, modifiers):
        if button != arcade.MOUSE_BUTTON_LEFT:
            return
            
        w, h = self.window.width, self.window.height
        s = h / 1080
        
        cx, cy = w * 0.08, h * 0.5
        radius = 60 * s
        btn_w, btn_h = 160 * s, 45 * s
        btn_x, btn_y = cx - (btn_w / 2), cy - radius - (60 * s)
        
        if self.is_player_turn:
            if btn_x <= x <= btn_x + btn_w and btn_y <= y <= btn_y + btn_h:
                self.is_player_turn = False
                self.turn_timer = 0.0
                return

        if not self.is_player_turn:
            return

        hit_hand = arcade.get_sprites_at_point((x, y), self.hand_sprite_list)
        if hit_hand:
            card = hit_hand[0]
            if self.player.active:
                self.player.active.deselect()
            if self.player.active == card:
                self.player.active = None
            else:
                self.player.active = card
                card.select()
            return

        hit_board = arcade.get_sprites_at_point((x, y), self.card_sprite_list)
        if hit_board:
            card = hit_board[0]
            if card.player == self.player:
                if self.player.active:
                    self.player.active.deselect()
                if self.player.active == card:
                    self.player.active = None
                else:
                    self.player.active = card
                    card.select()
                return
            elif card.player == self.enemy:
                if self.player.active and self.player.active in self.player.cards:
                    card.deal_damage(self.player.active)
                    self.player.active.deal_damage(card)
                    
                    if self.player.active.hp <= 0:
                        dead_card = self.player.active
                        self.player.cards.remove(dead_card)
                        self.card_sprite_list.remove(dead_card)
                        if dead_card.slot: dead_card.slot.remove_card()
                        self.discard_pile.append(dead_card)
                    
                    if card.hp <= 0:
                        dead_enemy = card
                        self.enemy.cards.remove(dead_enemy)
                        self.card_sprite_list.remove(dead_enemy)
                        if dead_enemy.slot: dead_enemy.slot.remove_card()

                    self.player.active.deselect()
                    self.player.active = None
                return

        hit_slots = arcade.get_sprites_at_point((x, y), self.slot_sprite_list)
        if hit_slots:
            slot = hit_slots[0]
            if self.player.active and self.player.active in self.player.hand:
                if slot.grid_y == 1 and slot.card is None:
                    if self.player.energy <= 0:
                        print("Не хватает энергии!")
                        return
                        
                    self.player.hand.remove(self.player.active)
                    self.hand_sprite_list.remove(self.player.active)
                    self.player.cards.append(self.player.active)
                    self.card_sprite_list.append(self.player.active)
                    
                    slot.add_card(self.player.active)
                    self.player.active.deselect()
                    self.player.active = None
                    self.player.energy -= 1
                return