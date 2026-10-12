# ============================================================
# Education.py — экран обучения (пока заглушка).
# Кнопка «Обучение» в главном меню теперь открывает его,
# а ESC возвращает обратно.
# ============================================================

import arcade


class EducationView(arcade.View):
    """Экран обучения (заглушка)."""

    def __init__(self):
        super().__init__()
        self.title = arcade.Text(
            "ОБУЧЕНИЕ", 0, 0, arcade.color.WHITE,
            font_size=40, font_name="Cyrillic Pixel-7",
            anchor_x="center", anchor_y="center",
        )
        self.hint = arcade.Text(
            "Скоро здесь появится обучение.  ESC — назад", 0, 0,
            arcade.color.LIGHT_GRAY,
            font_size=20, font_name="Cyrillic Pixel-7",
            anchor_x="center", anchor_y="center",
        )

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        self.title.x, self.title.y = w / 2, h / 2 + 30
        self.hint.x, self.hint.y = w / 2, h / 2 - 30
        self.title.draw()
        self.hint.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            # Импорт внутри метода — иначе циклический импорт с Menu.py
            from Menu import MainMenu
            self.window.show_view(MainMenu())