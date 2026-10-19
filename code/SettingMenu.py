# ============================================================
# SettingMenu.py — меню настроек с табами.
# ============================================================

import arcade
import arcade.gui
from Audio import update_music_volume
from menu_base import MenuView
from Settings import settings
from ui_widgets import ToggleButton, make_style
from utils import FONT_UI, apply_video_settings, get_monitor_info


class SettingMenu(MenuView):
    def __init__(self, return_to=None):
        super().__init__()
        self.current_tab = "audio"
        self.resolutions = self._get_available_resolutions()

        self.return_to = return_to # Запоминаем, откуда пришли
        self.current_tab = "audio"

        self.title_text = arcade.Text(
            text="НАСТРОЙКИ", x=0, y=0,
            color=arcade.color.WHITE,
            font_size=34, font_name=FONT_UI,
            anchor_x="center", anchor_y="top",
        )

    # ---------------- Разрешения ----------------

    def _get_available_resolutions(self):
        mon_w, mon_h, _ = get_monitor_info()
        base = [
            (1280, 720),
            (1366, 768),
            (1600, 900),
            (1920, 1080),
            (2560, 1440),
        ]
        options = [r for r in base if r[0] <= mon_w and r[1] <= mon_h]
        if (mon_w, mon_h) not in options:
            options.append((mon_w, mon_h))
        options.sort(key=lambda r: r[0] * r[1])
        return options

    # ---------------- Навигация / действия ----------------

    def _go_back(self):
        from MainMenu import MainMenu
        self.window.show_view(MainMenu())

        if self.return_to:
            # Если пришли из паузы, возвращаемся туда
            self.window.show_view(self.return_to)
        else:
            # Если из главного меню, идем туда
            from MainMenu import MainMenu
            self.window.show_view(MainMenu())

    def _switch_tab(self, tab_name):
        self.current_tab = tab_name
        self.request_rebuild()

    def _reset(self):
        settings.reset()
        apply_video_settings(self.window)
        self.request_rebuild()

    # ---------------- Обработчики настроек ----------------

    def _on_fullscreen_change(self, _is_fullscreen):
        apply_video_settings(self.window)
        if not settings.get("fullscreen"):
            try:
                self.window.set_exclusive_mouse(False)
            except Exception:  # noqa: BLE001, S110
                pass

    def _on_vsync_change(self, _enabled):
        apply_video_settings(self.window)

    def _on_resolution_change(self, value):
        try:
            w_str, h_str = value.split("x")
            settings.set("resolution_width", int(w_str))
            settings.set("resolution_height", int(h_str))
        except ValueError:
            return
        apply_video_settings(self.window)

    # ---------------- Раскладка ----------------

    def _layout(self):
        super()._layout()
        s = self.ui_scale()
        self.title_text.font_size = int(34 * s)
        self.title_text.x = self.window.width / 2
        self.title_text.y = self.window.height - int(24 * s)

    # ---------------- Построение UI ----------------

    def _build_ui(self):
        s = self.ui_scale()
        font_size = int(20 * s)
        self._layout()
        self.manager.clear()

        self._build_tabs(s, font_size)

        builders = {
            "audio": self._build_audio,
            "video": self._build_video,
            "gameplay": self._build_gameplay,
        }
        content = builders[self.current_tab](s)
        content_anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        content_anchor.add(
            child=content,
            anchor_x="center_x",
            anchor_y="center_y",
        )

        self._build_bottom(s, font_size)

    def _build_tabs(self, s, font_size):
        tab_style = make_style(font_size)
        active_style = make_style(font_size, arcade.color.WHITE, 2)

        tabs_box = arcade.gui.UIBoxLayout(
            vertical=False, space_between=int(15 * s)
        )
        for name, text in (("audio", "АУДИО"),
                           ("video", "ВИДЕО"),
                           ("gameplay", "ИГРА")):
            btn = arcade.gui.UIFlatButton(
                text=text, width=int(200 * s), height=int(50 * s),
                style=active_style if name == self.current_tab else tab_style,
            )

            @btn.event("on_click")
            def _go(event, tab=name):
                self._switch_tab(tab)

            tabs_box.add(btn)

        tabs_offset = int(24 * s + 34 * s * 2.0 + 16 * s)
        tabs_anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        tabs_anchor.add(
            child=tabs_box,
            anchor_x="center_x",
            anchor_y="top",
            align_y=-tabs_offset,
        )

    def _build_bottom(self, s, font_size):
        bottom_style = make_style(font_size)
        reset_btn = arcade.gui.UIFlatButton(
            text="СБРОС", width=int(200 * s), height=int(60 * s),
            style=bottom_style,
        )
        back_btn = arcade.gui.UIFlatButton(
            text="НАЗАД", width=int(200 * s), height=int(60 * s),
            style=bottom_style,
        )

        @reset_btn.event("on_click")
        def _on_reset(event):
            self._reset()

        @back_btn.event("on_click")
        def _on_back(event):
            self._go_back()

        bottom_box = arcade.gui.UIBoxLayout(
            vertical=False, space_between=int(30 * s)
        )
        bottom_box.add(reset_btn)
        bottom_box.add(back_btn)

        bottom_anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        bottom_anchor.add(
            child=bottom_box,
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=int(30 * s),
        )

    # ---------------- Табы ----------------

    def _build_audio(self, s):
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=int(24 * s))

        box.add(self._make_slider_row(
            "Общая громкость", "master_volume", s,
            on_change=lambda v: update_music_volume(),
        ))
        box.add(self._make_slider_row(
            "Музыка", "music_volume", s,
            on_change=lambda v: update_music_volume(),
        ))
        box.add(self._make_slider_row("Звуки", "sfx_volume", s))

        return box

    def _build_video(self, s):
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=int(24 * s))

        res_options = [f"{w}x{h}" for (w, h) in self.resolutions]
        saved_w = settings.get("resolution_width")
        saved_h = settings.get("resolution_height")
        current_res = f"{saved_w}x{saved_h}"
        if current_res not in res_options:
            closest = min(
                self.resolutions,
                key=lambda r: abs(r[0] - saved_w) + abs(r[1] - saved_h),
            )
            current_res = f"{closest[0]}x{closest[1]}"

        res_row = arcade.gui.UIBoxLayout(
            vertical=False, space_between=int(20 * s)
        )
        res_row.add(self._make_label("Разрешение", s))

        res_dropdown = arcade.gui.UIDropdown(
            default=current_res,
            options=res_options,
            width=int(250 * s),
            height=int(40 * s),
        )

        @res_dropdown.event("on_change")
        def _change_res(event):
            self._on_resolution_change(res_dropdown.value)

        res_row.add(res_dropdown)
        box.add(res_row)

        box.add(self._make_toggle_row(
            "Полный экран", "fullscreen", s,
            on_change=self._on_fullscreen_change,
        ))
        box.add(self._make_toggle_row(
            "Вертикальная синхронизация", "vsync", s,
            on_change=self._on_vsync_change,
        ))
        return box

    def _build_gameplay(self, s):
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=int(24 * s))
        box.add(self._make_toggle_row("Показывать FPS", "show_fps", s))
        box.add(self._make_toggle_row("Тряска экрана", "screen_shake", s))
        box.add(self._make_slider_row(
            "Скорость анимаций", "animation_speed", s,
            min_val=0.5, max_val=2.0,
            fmt=lambda v: f"x{v:.2f}",
        ))
        return box

    # ---------------- Строители строк ----------------

    def _make_label(self, text, s):
        return arcade.gui.UILabel(
            text=text,
            font_name=FONT_UI,
            font_size=int(20 * s),
            text_color=arcade.color.WHITE,
            width=int(420 * s),
        )

    def _make_slider_row(self, label_text, setting_key, s,
                         on_change=None, min_val=0.0, max_val=1.0, fmt=None):
        if fmt is None:
            fmt = lambda v: f"{round(v * 100)}%"

        row = arcade.gui.UIBoxLayout(
            vertical=False, space_between=int(20 * s)
        )
        row.add(self._make_label(label_text, s))

        current = settings.get(setting_key)
        current = min(max(current, min_val), max_val)
        slider = arcade.gui.UISlider(
            value=current,
            min_value=min_val,
            max_value=max_val,
            width=int(300 * s),
            height=int(30 * s),
        )

        value_label = arcade.gui.UILabel(
            text=fmt(current),
            font_name=FONT_UI,
            font_size=int(18 * s),
            text_color=arcade.color.LIGHT_GRAY,
            width=int(90 * s),
        )

        @slider.event("on_change")
        def _slider_change(event):
            v = slider.value
            settings.set(setting_key, v)
            value_label.text = fmt(v)
            if on_change:
                on_change(v)

        row.add(slider)
        row.add(value_label)
        return row

    def _make_toggle_row(self, label_text, setting_key, s, on_change=None):
        row = arcade.gui.UIBoxLayout(
            vertical=False, space_between=int(20 * s)
        )
        row.add(self._make_label(label_text, s))
        row.add(ToggleButton(
            setting_key=setting_key,
            on_change=on_change,
            font_size=int(20 * s),
            width=int(120 * s),
            height=int(48 * s),
        ))
        return row

    # ---------------- Lifecycle ----------------

    def on_hide_view(self):
        super().on_hide_view()
        settings.save()

    def on_draw(self):
        self.draw_background()
        arcade.draw_rect_filled(
            arcade.LRBT(0, self.window.width, 0, self.window.height),
            (0, 0, 0, 170),
        )
        self.title_text.draw()
        self.manager.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            try:
                self.window.set_exclusive_mouse(False)
            except Exception:  # noqa: BLE001, S110
                pass
            self._go_back()