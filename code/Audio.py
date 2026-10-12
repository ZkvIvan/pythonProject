# ============================================================
# Audio.py — звуки интерфейса и музыка меню.
# ============================================================

import arcade
from Settings import settings
from paths import asset


# ------------------------------------------------------------
# UI-звуки (hover, click)
# ------------------------------------------------------------
_UI_SOUNDS = None


def load_ui_sounds():
    global _UI_SOUNDS
    if _UI_SOUNDS is None:
        try:
            _UI_SOUNDS = (
                arcade.load_sound(asset("sounds", "hover_opt.wav")),
                arcade.load_sound(asset("sounds", "click_opt.wav")),
            )
            print("[sound] UI-звуки загружены")
        except Exception as e:
            print(f"[sound] нет UI-звуков: {e}")
            _UI_SOUNDS = (None, None)
    return _UI_SOUNDS


def play_sfx(sound, volume=None):
    if not sound:
        return
    try:
        if volume is None:
            volume = settings.get("master_volume") * settings.get("sfx_volume")
        arcade.play_sound(sound, volume=volume)
    except Exception as e:
        print(f"[sound] не удалось проиграть: {e}")


# ------------------------------------------------------------
# Музыка меню
# Без streaming=True — иначе source нельзя воспроизвести повторно.
# ------------------------------------------------------------
_MUSIC = None
_MUSIC_PLAYER = None


def load_music():
    global _MUSIC
    if _MUSIC is None:
        try:
            _MUSIC = arcade.load_sound(
                asset("sounds", "main_menu_ambient_fixed1.ogg"),
                streaming=False,
            )
            print("[music] музыка загружена")
        except Exception as e:
            print(f"[music] нет музыки: {e}")
            _MUSIC = None
    return _MUSIC


def start_menu_music():
    global _MUSIC_PLAYER
    if _MUSIC_PLAYER is not None and _MUSIC_PLAYER.playing:
        return
    music = load_music()
    if music is None:
        return
    try:
        volume = settings.get("master_volume") * settings.get("music_volume")
        _MUSIC_PLAYER = arcade.play_sound(music, volume=volume, loop=True)
        print("[music] старт")
    except Exception as e:
        print(f"[music] не удалось запустить: {e}")
        _MUSIC_PLAYER = None


def stop_menu_music():
    global _MUSIC_PLAYER
    if _MUSIC_PLAYER is not None:
        try:
            _MUSIC_PLAYER.pause()
        except Exception:
            pass
        _MUSIC_PLAYER = None
        print("[music] стоп")


def update_music_volume():
    global _MUSIC_PLAYER
    if _MUSIC_PLAYER is not None:
        try:
            _MUSIC_PLAYER.volume = (
                settings.get("master_volume") * settings.get("music_volume")
            )
        except Exception:
            pass