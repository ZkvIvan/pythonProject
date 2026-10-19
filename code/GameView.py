# ============================================================
# GameView.py — заготовки сцен: игра, пауза, победа, проигрыш.
# ИСПРАВЛЕНО: draw_text заменён на arcade.Text (убирает
# PerformanceWarning и работает быстрее).
# ============================================================
import random
import time

import arcade
from arcade import gl
import arcade.gui

from classes.player import Player
from classes.slot import Slot
from classes.card import Card
from classes.grid import Grid


class GameView(arcade.View):
    """Основная игровая сцена (пока пустая)."""
    def __init__(self):
        super().__init__()
        self.card_sprite_list = arcade.SpriteList()
        self.heart_sprite_list = arcade.SpriteList()
        self.sword_sprite_list = arcade.SpriteList()
        self.slot_sprite_list = arcade.SpriteList()

        self.grid = Grid(self, 13, 4)

        for i in range(4, 10):
            for j in [1, 3]:
                self.grid.add_slot(i, j, Slot(self))

        for i in range(5, 9):
            for j in [2]:
                self.grid.add_slot(i, j, Slot(self))

        self.player = Player(self)
        self.enemy = Player(self, is_enemy=True)

        for i in range(6):
            q = Card(self, self.player, random.randint(1, 15), random.randint(1, 15), 'card_test')
            self.player.cards.append(q)
            self.grid.add_card(i + 4, 1, q)

        for i in range(6):
            q = Card(self, self.enemy, random.randint(1, 15), random.randint(1, 15), 'card_test')
            self.enemy.cards.append(q)
            self.grid.add_card(i + 4, 3, q)

        for i in range(4):
            q = Card(self, self.enemy, random.randint(1, 15), random.randint(1, 15), 'card_test')
            self.enemy.cards.append(q)
            self.grid.add_card(i + 5, 2, q)

        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        end_button = arcade.gui.UIFlatButton(text="End turn", width=300, height=150)
        end_button.on_click = self.end_turn
        self.layout = arcade.gui.UIAnchorLayout(
        )

        self.layout.add(end_button.with_padding(all=50), anchor_x='left', anchor_y='bottom')
        self.manager.add(
            self.layout
        )

    def on_draw(self):
        self.clear()

        self.layout.width = self.window.width
        self.layout.height = self.window.height

        self.player.on_draw()
        self.enemy.on_draw()
        self.grid.on_draw()

        self.slot_sprite_list.draw(filter=gl.NEAREST)
        self.card_sprite_list.draw(filter=gl.NEAREST)
        self.heart_sprite_list.draw(filter=gl.NEAREST)
        self.sword_sprite_list.draw(filter=gl.NEAREST)

        self.player.draw()
        self.enemy.draw()

        self.manager.draw()

    def end_turn(self, *args):
        self.player.moves = 3

        for x in range(5, 9):
            if self.grid.slots[(x, 2)].card is not None and self.grid.slots[(x, 2)].card.player == self.player:
                self.enemy.deal_damage(self.grid.slots[(x, 2)].card)

        for _ in range(3):
            self.enemy.select_best()
            if self.enemy.active:
                print('damage', self.enemy.active.strength)
                most_dangerous = self.player.get_most_dangerous()
                #time.sleep(0.5)
                if most_dangerous:
                    most_dangerous.deal_damage(self.enemy.active)
                else:
                    for x in range(5, 9):
                        if not self.grid.slots[(x, 2)].card:
                            print('MOVED')
                            self.enemy.active.slot.remove_card()
                            self.grid.slots[(x, 2)].add_card(self.enemy.active)
                            #time.sleep(0.5)
                    #self.player.deal_damage(self.enemy.active)
            else:
                break

        for x in range(5, 9):
            if self.grid.slots[(x, 2)].card is not None and self.grid.slots[(x, 2)].card.player == self.enemy:
                self.player.deal_damage(self.grid.slots[(x, 2)].card)

    def on_mouse_press(self, x, y, button, modifiers):
        if button == arcade.MOUSE_BUTTON_LEFT:
            # click card
            hit_sprites = arcade.get_sprites_at_point((x, y), self.card_sprite_list)

            for sprite in hit_sprites:
                if sprite.slot.y > 2:
                    break

                if sprite.player == self.player:
                    if self.player.active:
                        self.player.active.deselect()

                    self.player.active = sprite
                    sprite.select()
                else:
                    self.player.moves -= 1
                    print(self.player.moves)

                    if self.player.active:
                        sprite.deal_damage(self.player.active)
                        self.player.active.deal_damage(sprite)

                    if not self.player.can_move():
                        self.end_turn()

            if hit_sprites:
                return

            # click slot
            hit_sprites = arcade.get_sprites_at_point((x, y), self.slot_sprite_list)

            for sprite in hit_sprites:
                if sprite.y > 2:
                    break

                if self.player.active:
                    self.player.active.slot.remove_card()
                    sprite.add_card(self.player.active)

    def on_win(self):
        self.window.show_view(WinMenu())

    def on_loose(self):
        self.window.show_view(LooseMenu())


class PauseMenu(arcade.View):
    """Меню паузы (пока пустое)."""
    pass


class WinMenu(arcade.View):
    """Экран победы."""
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
        self.title_text = arcade.Text(
            text="You Win!",
            x=0, y=0,
            color=arcade.color.GREEN,
            font_size=50,
            font_name="Cyrillic Pixel-7",
            anchor_x="center", anchor_y="center",
        )

    def on_draw(self):
        self.clear()
        self.title_text.x = self.window.width / 2
        self.title_text.y = self.window.height / 2
        self.title_text.draw()


class LooseMenu(arcade.View):
    """Экран поражения."""
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
        self.title_text = arcade.Text(
            text="You Lose!",
            x=0, y=0,
            color=arcade.color.RED,
            font_size=50,
            font_name="Cyrillic Pixel-7",
            anchor_x="center", anchor_y="center",
        )

    def on_draw(self):
        self.clear()
        self.title_text.x = self.window.width / 2
        self.title_text.y = self.window.height / 2
        self.title_text.draw()