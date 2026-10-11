import arcade
from Menu import MainMenu, SettingMenu, StartWindow, get_monitor_info
from GameView import GameView, PauseMenu, WinMenu, LooseMenu

game_name = "build_1"

def main():
    width, height, hz = get_monitor_info()
    window = StartWindow(width, height, game_name, update_rate=1/hz)
    menu_view = MainMenu()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()