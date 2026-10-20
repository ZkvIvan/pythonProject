import arcade

from Audio import start_menu_music


class EducationView(arcade.View):
    def __init__(self):
        super().__init__()
        self.title = arcade.Text(
            "ОБУЧЕНИЕ", 0, 0, arcade.color.WHITE,
            font_size=40, font_name="Cyrillic Pixel-7",
            anchor_x="center", anchor_y="center",
        )
        self.hint = arcade.Text(
            "Карты, деньги, два обучения", 0, 0,
            arcade.color.LIGHT_GRAY,
            font_size=20, font_name="Cyrillic Pixel-7",
            anchor_x="center", anchor_y="center",
        )

    def on_show_view(self):
        arcade.set_background_color(arcade.color.BLACK)
        start_menu_music()

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        self.title.x, self.title.y = w / 2, h / 2 + 30
        self.hint.x, self.hint.y = w / 2, h / 2 - 30
        self.title.draw()
        self.hint.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from MainMenu import MainMenu
            self.window.show_view(MainMenu())