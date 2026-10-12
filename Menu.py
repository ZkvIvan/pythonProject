# ============================================================
# Menu.py — главное меню и меню настроек.
# ============================================================

import math
import os

import arcade
import arcade.gui
import pyglet
import pyglet.display

from Settings import settings
from GameView import GameView
from Education import EducationView

# ------------------------------------------------------------
# Пути и ресурсы
# ------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_TITLE = "Vyaz Pixel"
FONT_UI = "Cyrillic Pixel-7"

BG_FRAME_DURATION = 0.15


def asset(*parts):
    return os.path.join(BASE_DIR, *parts)


def _load_font(file_names):
    for folder in ("fonts", ""):
        for name in file_names:
            path = asset(folder, name)
            if os.path.exists(path):
                arcade.load_font(path)
                return True
    print(f"[font] не найден ни один из файлов: {file_names}")
    return False


_load_font(["Vyaz Pixel.ttf", "Vyaz_Pixel.ttf"])
_load_font(["cyrillic_pixel-7.ttf", "Cyrillic Pixel-7.ttf"])


# ============================================================
# get_monitor_info
# ============================================================
def get_monitor_info():
    try:
        width, height = arcade.get_display_size()
    except Exception as e:
        print(f"[monitor] не удалось узнать размер дисплея: {e}")
        width, height = 1920, 1080

    refresh_rate = 60
    try:
        screen = pyglet.display.get_display().get_default_screen()
        rate = screen.get_mode().rate
        if rate and rate > 0:
            refresh_rate = int(rate)
    except Exception as e:
        print(f"[monitor] fallback 60Hz: {e}")
    return width, height, refresh_rate


# ============================================================
# apply_video_settings — применяет видео-настройки к окну.
# ИСПРАВЛЕНО: теперь ещё управляет захватом мыши.
#   - В полноэкранном режиме — захватываем мышь.
#   - В оконном — отпускаем.
# (В WSLg это может не помочь — там своя проблема с мышью,
#  лечится только перезапуском WSL. На нативном Windows работает.)
# ============================================================
def apply_video_settings(window):
    try:
        mon_w, mon_h, _ = get_monitor_info()
        window.set_vsync(bool(settings.get("vsync")))

        if settings.get("fullscreen"):
            if not window.fullscreen:
                window.set_fullscreen(True)
            window.set_exclusive_mouse(True)
        else:
            if window.fullscreen:
                window.set_fullscreen(False)
            window.set_exclusive_mouse(False)
            w = min(int(settings.get("resolution_width")), mon_w)
            h = min(int(settings.get("resolution_height")), mon_h)
            window.set_size(w, h)
            window.center_window()
    except Exception as e:
        print(f"[video] не удалось применить настройки: {e}")


# ============================================================
# Звуки интерфейса
# ============================================================
_UI_SOUNDS = None


def load_ui_sounds():
    global _UI_SOUNDS
    if _UI_SOUNDS is None:
        try:
            _UI_SOUNDS = (
                arcade.load_sound(asset("sounds", "hover.wav")),
                arcade.load_sound(asset("sounds", "click.wav")),
            )
            print("[sound] звуки загружены")
        except Exception as e:
            print(f"[sound] нет звуков: {e}")
            _UI_SOUNDS = (None, None)
    return _UI_SOUNDS


def play_sfx(sound):
    if not sound:
        return
    try:
        volume = settings.get("master_volume") * settings.get("sfx_volume")
        arcade.play_sound(sound, volume=volume)
    except Exception as e:
        print(f"[sound] не удалось проиграть: {e}")


# ============================================================
# Кадры фоновой анимации
# ============================================================
_BG_FRAMES = None


def load_bg_frames():
    global _BG_FRAMES
    if _BG_FRAMES is None:
        try:
            _BG_FRAMES = [
                arcade.load_texture(asset("images", "MainMenu", f"{n}.png"))
                for n in range(1, 11)
            ]
        except Exception as e:
            print(f"[bg] не удалось загрузить фон: {e}")
            _BG_FRAMES = []
    return _BG_FRAMES


# ============================================================
# Стили кнопок
# ============================================================
GRAY = (90, 90, 90, 255)
CLEAR = (0, 0, 0, 0)


def make_style(font_size, normal_border=GRAY, normal_border_width=1,
               font_color=arcade.color.WHITE):
    UIStyle = arcade.gui.UIFlatButton.UIStyle

    def state(color, border, border_width):
        return UIStyle(
            font_color=color,
            font_name=FONT_UI,
            font_size=font_size,
            bg=CLEAR,
            border=border,
            border_width=border_width,
        )

    return {
        "normal": state(font_color, normal_border, normal_border_width),
        "hover": state(arcade.color.WHITE, arcade.color.WHITE, 2),
        "press": state(arcade.color.LIGHT_GRAY, arcade.color.LIGHT_GRAY, 2),
    }


# ============================================================
# AnimatedBackground
# ============================================================
class AnimatedBackground(arcade.Sprite):
    def __init__(self, textures, frame_duration=BG_FRAME_DURATION, scale=1.0):
        super().__init__(textures[0], scale=scale)
        self.frames = textures
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.timer = 0.0

    def update_animation(self, delta_time=1 / 60):
        self.timer += delta_time
        if self.timer >= self.frame_duration:
            self.timer -= self.frame_duration
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.texture = self.frames[self.current_frame]


# ============================================================
# SoundButton — кнопка со звуками hover/click.
# ИСПРАВЛЕНО:
#   - on_click теперь вызывает super().on_click(event)
#   - _was_hovered инициализируется сразу в __init__
# ============================================================
class SoundButton(arcade.gui.UIFlatButton):
    def __init__(self, *args, hover_sound=None, click_sound=None,
                 callback=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hover_sound = hover_sound
        self.click_sound = click_sound
        self.callback = callback
        # ИСПРАВЛЕНО: сразу ставим текущее значение hovered,
        # чтобы первый кадр не считался «переходом» и не играл звук
        self._was_hovered = bool(self.hovered)

    def on_event(self, event):
        result = super().on_event(event)
        hovered = bool(self.hovered)
        if hovered and not self._was_hovered:
            play_sfx(self.hover_sound)
        self._was_hovered = hovered
        return result

    def on_click(self, event):
        # ИСПРАВЛЕНО: сначала даём базовому классу обработать событие,
        # потом играем звук и вызываем callback
        super().on_click(event)
        play_sfx(self.click_sound)
        if self.callback:
            self.callback(event)


# ============================================================
# ToggleButton — кнопка-переключатель ВКЛ/ВЫКЛ.
# ИСПРАВЛЕНО: on_click теперь вызывает super().on_click(event)
# ============================================================
class ToggleButton(arcade.gui.UIFlatButton):
    @staticmethod
    def _style_for(state, font_size):
        if state:
            return make_style(font_size, arcade.color.WHITE, 2,
                              arcade.color.WHITE)
        return make_style(font_size, GRAY, 1, (150, 150, 150, 255))

    def __init__(self, *, setting_key, on_change=None, font_size=20,
                 width=120, height=48):
        state = bool(settings.get(setting_key))
        super().__init__(
            text="ВКЛ" if state else "ВЫКЛ",
            width=width, height=height,
            style=ToggleButton._style_for(state, font_size),
        )
        self.setting_key = setting_key
        self._on_change_cb = on_change
        self._font_size = font_size

    def on_click(self, event):
        # ИСПРАВЛЕНО: сначала super(), потом своя логика
        super().on_click(event)
        new_state = not settings.get(self.setting_key)
        settings.set(self.setting_key, new_state)
        self.text = "ВКЛ" if new_state else "ВЫКЛ"
        self.style = ToggleButton._style_for(new_state, self._font_size)
        self.trigger_render()
        if self._on_change_cb:
            self._on_change_cb(new_state)


# ============================================================
# StartWindow
# ============================================================
class StartWindow(arcade.Window):
    MIN_WIDTH = 1280
    MIN_HEIGHT = 720

    def __init__(self, width, height,
                 update_rate=1 / 60,
                 title="VYAZ SUDBY",
                 fullscreen=False,
                 resizable=True,
                 antialiasing=True,
                 vsync=True):
        super().__init__(
            width=width,
            height=height,
            title=title,
            fullscreen=fullscreen,
            resizable=resizable,
            update_rate=update_rate,
            antialiasing=antialiasing,
            vsync=vsync,
        )
        mon_w, mon_h, _ = get_monitor_info()
        self.set_minimum_size(min(self.MIN_WIDTH, mon_w),
                              min(self.MIN_HEIGHT, mon_h))
        if not fullscreen:
            self.center_window()


# ============================================================
# MenuView — общая база для меню.
# ИСПРАВЛЕНО: в on_show_view принудительно отпускаем мышь,
# чтобы в меню курсор всегда работал (важно для WSLg).
# ============================================================
class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.time = 0.0
        self.manager = arcade.gui.UIManager()
        self._active = False
        self._rebuild_pending = False

        self.background_list = arcade.SpriteList()
        self.animated_bg = None
        frames = load_bg_frames()
        if frames:
            self.animated_bg = AnimatedBackground(frames)
            self.background_list.append(self.animated_bg)

    def ui_scale(self):
        return max(1.0, min(2.0, self.window.height / 720))

    def request_rebuild(self):
        if self._rebuild_pending:
            return
        self._rebuild_pending = True
        pyglet.clock.schedule_once(self._do_rebuild, 0)

    def _do_rebuild(self, _dt):
        self._rebuild_pending = False
        if self._active:
            self._build_ui()

    def _build_ui(self):
        raise NotImplementedError

    def _layout(self):
        if self.animated_bg is None:
            return
        w, h = self.window.width, self.window.height
        tex = self.animated_bg.texture
        self.animated_bg.scale = max(w / tex.width, h / tex.height)
        self.animated_bg.center_x = w / 2
        self.animated_bg.center_y = h / 2

    def on_show_view(self):
        self._active = True
        arcade.set_background_color(arcade.color.BLACK)
        # ИСПРАВЛЕНО: в меню мышь всегда свободна
        try:
            self.window.set_exclusive_mouse(False)
        except Exception:
            pass
        self.manager.enable()
        self._layout()
        self._build_ui()

    def on_hide_view(self):
        self._active = False
        self.manager.disable()

    def on_resize(self, width, height):
        super().on_resize(width, height)
        self._layout()
        self.request_rebuild()

    def on_update(self, delta_time):
        self.time += delta_time
        if self.animated_bg is not None:
            speed = max(0.1, settings.get("animation_speed"))
            self.animated_bg.update_animation(delta_time * speed)

    def draw_background(self):
        self.clear()
        self.background_list.draw(pixelated=True)


# ============================================================
# MainMenu
# ============================================================
class MainMenu(MenuView):
    def __init__(self):
        super().__init__()
        self.hover_sound, self.click_sound = load_ui_sounds()

        self.title_shadow = arcade.Text(
            text="VYAZ SUDBY", x=0, y=0,
            color=arcade.color.BLACK,
            font_size=64, font_name=FONT_TITLE,
            anchor_x="left", anchor_y="top",
        )
        self.title_text = arcade.Text(
            text="VYAZ SUDBY", x=0, y=0,
            color=arcade.color.WHITE,
            font_size=64, font_name=FONT_TITLE,
            anchor_x="left", anchor_y="top",
        )

    def _start_game(self, _event):
        self.window.show_view(GameView())

    def _open_settings(self, _event):
        self.window.show_view(SettingMenu())

    def _open_education(self, _event):
        self.window.show_view(EducationView())

    def _exit(self, _event):
        arcade.exit()

    def _build_ui(self):
        s = self.ui_scale()
        w = self.window.width

        gap = int(30 * s)
        btn_w = int(min(280 * s, (w * 0.94 - 3 * gap) / 4))
        btn_h = int(100 * s)
        style = make_style(int(28 * s), CLEAR, 0)

        items = [
            ("Начать игру", self._start_game),
            ("Настройки", self._open_settings),
            ("Обучение", self._open_education),
            ("Выход", self._exit),
        ]

        h_box = arcade.gui.UIBoxLayout(vertical=False, space_between=gap)
        for text, callback in items:
            h_box.add(SoundButton(
                text=text, width=btn_w, height=btn_h, style=style,
                hover_sound=self.hover_sound, click_sound=self.click_sound,
                callback=callback,
            ))

        self.manager.clear()
        anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        anchor.add(
            child=h_box,
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=int(80 * s),
        )

    def _layout(self):
        super()._layout()
        w, h = self.window.width, self.window.height
        font_size = max(24, int(h * 0.1))
        margin_x = int(w * 0.03)
        margin_y = int(h * 0.05)

        self.title_text.font_size = font_size
        self.title_text.x = margin_x
        self.title_text.y = h - margin_y

        self.title_shadow.font_size = font_size
        self.title_shadow.x = margin_x + 4
        self.title_shadow.y = h - margin_y - 4

    def on_draw(self):
        self.draw_background()

        alpha = 200 + int(math.sin(self.time * 2) * 55)
        self.title_text.color = (255, 255, 255, alpha)
        self.title_shadow.draw()
        self.title_text.draw()

        self.manager.draw()


# ============================================================
# SettingMenu
# ============================================================
class SettingMenu(MenuView):
    def __init__(self):
        super().__init__()
        self.current_tab = "audio"
        self.resolutions = self._get_available_resolutions()

        self.title_text = arcade.Text(
            text="НАСТРОЙКИ", x=0, y=0,
            color=arcade.color.WHITE,
            font_size=34, font_name=FONT_UI,
            anchor_x="center", anchor_y="top",
        )

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

    def _go_back(self):
        self.window.show_view(MainMenu())

    def _switch_tab(self, tab_name):
        self.current_tab = tab_name
        self.request_rebuild()

    def _reset(self):
        settings.reset()
        apply_video_settings(self.window)
        self.request_rebuild()

    def _on_fullscreen_change(self, _is_fullscreen):
        apply_video_settings(self.window)
        # Если вышли из фуллскрина — отпускаем мышь
        if not settings.get("fullscreen"):
            try:
                self.window.set_exclusive_mouse(False)
            except Exception:
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

    def _layout(self):
        super()._layout()
        s = self.ui_scale()
        self.title_text.font_size = int(34 * s)
        self.title_text.x = self.window.width / 2
        self.title_text.y = self.window.height - int(24 * s)

    def _build_ui(self):
        s = self.ui_scale()
        font_size = int(20 * s)
        self._layout()
        self.manager.clear()

        # --- Табы под заголовком ---
        tab_style = make_style(font_size)
        active_style = make_style(font_size, arcade.color.WHITE, 2)

        tabs_box = arcade.gui.UIBoxLayout(vertical=False,
                                          space_between=int(15 * s))
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

        # ИСПРАВЛЕНО: множитель 2.0 вместо 1.4 — пиксельные шрифты
        # имеют большой внутренний padding, старая формула давала
        # пересечение с заголовком.
        tabs_offset = int(24 * s + 34 * s * 2.0 + 16 * s)
        tabs_anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        tabs_anchor.add(
            child=tabs_box,
            anchor_x="center_x",
            anchor_y="top",
            align_y=-tabs_offset,
        )

        # --- Контент таба ---
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

        # --- СБРОС / НАЗАД ---
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

        bottom_box = arcade.gui.UIBoxLayout(vertical=False,
                                            space_between=int(30 * s))
        bottom_box.add(reset_btn)
        bottom_box.add(back_btn)

        bottom_anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        bottom_anchor.add(
            child=bottom_box,
            anchor_x="center_x",
            anchor_y="bottom",
            align_y=int(30 * s),
        )

    def _build_audio(self, s):
        box = arcade.gui.UIBoxLayout(vertical=True, space_between=int(24 * s))
        box.add(self._make_slider_row("Общая громкость", "master_volume", s))
        box.add(self._make_slider_row("Музыка", "music_volume", s))
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

        res_row = arcade.gui.UIBoxLayout(vertical=False,
                                         space_between=int(20 * s))
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

        row = arcade.gui.UIBoxLayout(vertical=False, space_between=int(20 * s))
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
        row = arcade.gui.UIBoxLayout(vertical=False, space_between=int(20 * s))
        row.add(self._make_label(label_text, s))
        row.add(ToggleButton(
            setting_key=setting_key,
            on_change=on_change,
            font_size=int(20 * s),
            width=int(120 * s),
            height=int(48 * s),
        ))
        return row

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
            # ИСПРАВЛЕНО: при выходе отпускаем мышь
            try:
                self.window.set_exclusive_mouse(False)
            except Exception:
                pass
            self._go_back()