# ============================================================
# GameView.py — заготовки сцен: игра, пауза, победа, проигрыш.
# ИСПРАВЛЕНО: draw_text заменён на arcade.Text (убирает
# PerformanceWarning и работает быстрее).
# ============================================================

import arcade


class GameView(arcade.View):
    """Основная игровая сцена (пока пустая)."""
    pass


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