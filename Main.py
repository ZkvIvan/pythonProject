# ============================================================
# Main.py — точка входа в игру.
# Здесь создаётся окно, показывается главное меню и запускается
# главный цикл arcade.
# ============================================================

# ВАЖНО: настройки pyglet для звука должны быть установлены ДО import arcade,
# иначе pyglet уже выберет драйвер по умолчанию и настройка не подействует.
import pyglet
# Список драйверов по приоритету: pulse → openal → directsound → silent.
# silent — «заглушка», если ни один драйвер не запустился.
pyglet.options['audio'] = ('pulse', 'openal', 'directsound', 'silent')

import arcade
from Menu import MainMenu, StartWindow, get_monitor_info
from Settings import settings


def main():
    # Берём сохранённые настройки. Если файла нет — это дефолты.
    # Не даём окну быть больше монитора (в settings.json может лежать
    # разрешение от другого экрана, например 2560x1440 на ноутбуке).
    mon_w, mon_h, _ = get_monitor_info()
    width = min(settings.get("resolution_width"), mon_w)
    height = min(settings.get("resolution_height"), mon_h)
    fullscreen = settings.get("fullscreen")
    vsync = settings.get("vsync")

    # Создаём окно с нужными параметрами
    window = StartWindow(
        width=width,
        height=height,
        fullscreen=fullscreen,
        vsync=vsync,
        title="NightFall",
    )

    # Показываем главное меню как активную сцену
    window.show_view(MainMenu())

    # Главный цикл — работает, пока окно открыто
    arcade.run()


# Запускаем main() только если файл запущен напрямую (не импортирован)
if __name__ == "__main__":
    main()