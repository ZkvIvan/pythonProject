import arcade
import arcade.gui
from Audio import start_menu_music
from menu_base import MenuView
from Settings import settings  # noqa: F401
from ui_widgets import CLEAR, SoundButton, make_style


class PauseMenu(MenuView):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view
        
        self.title_text = arcade.Text(
            text="ПАУЗА", x=0, y=0,
            color=arcade.color.WHITE,
            font_size=50, font_name="Vyaz Pixel",
            anchor_x="center", anchor_y="center",
        )

    def _resume(self, _event):
        self.window.show_view(self.game_view)

    def _open_settings(self, _event):
        from SettingMenu import SettingMenu
        self.window.show_view(SettingMenu(return_to=self))

    def _go_to_main_menu(self, _event):
        from MainMenu import MainMenu
        self.window.show_view(MainMenu())

    def _exit_game(self, _event):
        arcade.exit()


    def _build_ui(self):
        s = self.ui_scale()
        
        btn_w = int(300 * s)
        btn_h = int(80 * s)
        style = make_style(int(28 * s), CLEAR, 0)

        items = [
            ("Продолжить", self._resume),
            ("Настройки", self._open_settings),
            ("В главное меню", self._go_to_main_menu),
            ("Выход", self._exit_game),
        ]

        v_box = arcade.gui.UIBoxLayout(vertical=True, space_between=int(20 * s))
        for text, callback in items:
            v_box.add(SoundButton(
                text=text, width=btn_w, height=btn_h, style=style,
                hover_sound=self.hover_sound, click_sound=self.click_sound,
                callback=callback,
            ))

        self.manager.clear()
        anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        anchor.add(
            child=v_box,
            anchor_x="center_x",
            anchor_y="center_y",
        )

    def _layout(self):
        self.title_text.x = self.window.width / 2
        self.title_text.y = self.window.height - int(100 * self.ui_scale())

    def on_show_view(self):
        
        self._active = True
        self.manager.enable()
        self._build_ui()
        start_menu_music()

    def on_draw(self):
        self.game_view.on_draw()

        arcade.draw_rect_filled(
            arcade.LRBT(0, self.window.width, 0, self.window.height),
            (0, 0, 0, 200),
        )

        self.title_text.draw()
        self.manager.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self._resume(None)