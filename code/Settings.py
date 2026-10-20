import json
from paths import data

SETTINGS_PATH = data("settings.json")


DEFAULT_SETTINGS = {
    "master_volume": 1.0,
    "music_volume": 0.7,
    "sfx_volume": 1.0,

    "resolution_width": 1280,
    "resolution_height": 720,
    "fullscreen": False,
    "vsync": True,

    "show_fps": False,
    "screen_shake": True,
    "animation_speed": 1.0,
}


class Settings:
    def __init__(self):
        self.data = dict(DEFAULT_SETTINGS)
        self.load()

    def load(self):
        import os
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        if not os.path.exists(SETTINGS_PATH):
            print("[settings] файла нет, используем дефолт")
            return
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            for key in DEFAULT_SETTINGS:
                if key in loaded:
                    self.data[key] = loaded[key]
            print(f"[settings] загружено из {SETTINGS_PATH}")
        except Exception as e:
            print(f"[settings] не удалось загрузить: {e}. Используем дефолт.")
            self.data = dict(DEFAULT_SETTINGS)

    def save(self):
        try:
            with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            print(f"[settings] сохранено в {SETTINGS_PATH}")
        except Exception as e:
            print(f"[settings] не удалось сохранить: {e}")

    def get(self, key):
        return self.data.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key, value):
        self.data[key] = value

    def reset(self):
        self.data = dict(DEFAULT_SETTINGS)


settings = Settings()