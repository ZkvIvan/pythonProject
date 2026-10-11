import arcade

class GameView(arcade.View):
    #ui + game
    pass

class PauseMenu(arcade.View):
    pass
    #кноки в меню и в настройки

class WinMenu(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
    def on_draw(self):
        self.clear()
        arcade.draw_text("You Win!", self.window.width / 2, self.window.height / 2,
                         arcade.color.GREEN, font_size=50, anchor_x="center", anchor_y="center")
    #кнопка в меню

class LooseMenu(arcade.View):
    def __init__(self):
        super().__init__()
        arcade.set_background_color(arcade.color.BLACK)
    def on_draw(self):
        self.clear()
        arcade.draw_text("You Lose!", self.window.width / 2, self.window.height / 2,
                         arcade.color.RED, font_size=50, anchor_x="center", anchor_y="center")
    #кнопка в меню
