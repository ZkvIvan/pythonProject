# ============================================================
# Settings.py — хранилище настроек игры
# Настройки хранятся в JSON-файле рядом с игрой и загружаются
# при первом импорте модуля.
# ============================================================

import json
import os

# Путь к папке, где лежит этот файл (Menu.py, Main.py и т.д.)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Полный путь к файлу настроек: gameProject/settings.json
SETTINGS_PATH = os.path.join(BASE_DIR, "settings.json")


# Значения по умолчанию. Если файла settings.json нет, или в нём
# отсутствуют какие-то ключи, используются эти значения.
DEFAULT_SETTINGS = {
    # --- Аудио ---
    "master_volume": 1.0,   # общая громкость: 0.0 — тишина, 1.0 — максимум
    "music_volume": 0.7,    # громкость музыки
    "sfx_volume": 1.0,      # громкость звуковых эффектов

    # --- Видео ---
    "resolution_width": 1280,   # ширина окна в пикселях
    "resolution_height": 720,   # высота окна в пикселях
    "fullscreen": False,        # полноэкранный режим
    "vsync": True,              # вертикальная синхронизация

    # --- Геймплей ---
    "show_fps": False,          # показывать ли FPS на экране
    "screen_shake": True,       # тряска экрана при ударах
    "animation_speed": 1.0,     # множитель скорости анимаций: 0.5 — медленно, 2.0 — быстро
}


class Settings:
    """
    Класс, который хранит настройки в self.data и умеет
    загружать их из файла и сохранять обратно.
    """

    def __init__(self):
        # Копируем словарь дефолтов, чтобы не менять оригинал
        self.data = dict(DEFAULT_SETTINGS)
        # Сразу пытаемся загрузить сохранённые настройки
        self.load()

    def load(self):
        """
        Загружает настройки из settings.json.
        Если файла нет — оставляет дефолты.
        Если файл битый — печатает ошибку и откатывается на дефолты.
        """
        # Если файла ещё нет — используем дефолты, ничего не делаем
        if not os.path.exists(SETTINGS_PATH):
            print("[settings] файла нет, используем дефолт")
            return

        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            # Обновляем только те ключи, которые есть в дефолтах.
            # Это защита от «мусорных» ключей в файле.
            for key in DEFAULT_SETTINGS:
                if key in loaded:
                    self.data[key] = loaded[key]

            print(f"[settings] загружено из {SETTINGS_PATH}")

        except Exception as e:
            print(f"[settings] не удалось загрузить: {e}. Используем дефолт.")
            self.data = dict(DEFAULT_SETTINGS)

    def save(self):
        """Сохраняет текущие настройки в settings.json."""
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                # indent=2 — красиво отформатированный JSON
                # ensure_ascii=False — русские буквы не превращаются в \uXXXX
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"[settings] сохранено в {SETTINGS_PATH}")
        except Exception as e:
            print(f"[settings] не удалось сохранить: {e}")

    def get(self, key):
        """Возвращает значение настройки по ключу."""
        return self.data.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        """Устанавливает значение настройки в памяти."""
        self.data[key] = value

    def reset(self):
        """Возвращает все настройки к дефолтам (без сохранения на диск)."""
        self.data = dict(DEFAULT_SETTINGS)


# Единственный экземпляр на всю игру. Импортируется как `from Settings import settings`.
settings = Settings()