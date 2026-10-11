import arcade
import pyglet
import pyglet.display

def get_monitor_info():
    width, height = arcade.get_display_size()

    refresh_rate = 60

    screen = pyglet.display.get_display().get_default_screen()
    rate = screen.get_mode().rate // 1000 # почему в мили герцах?????
    if rate and rate > 0:
        refresh_rate = rate

    return width, height, refresh_rate

class StartWindow(arcade.Window):
    def __init__(self, width, height, title,
                 update_rate=1/60, fullscreen=False,
                 resizable=True, antialiasing=True, vsync=True):
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

class AnimatedBackground(arcade.Sprite):
    def __init__(self, textures, frame_duration=0.1, scale=1.0):
        super().__init__(textures[0], scale=scale) 
        self.textures = textures
        self.frame_duration = frame_duration
        self.current_frame = 0
        self.timer = 0.0

    def update_animation(self, delta_time=1/60):
        self.timer += delta_time
        if self.timer >= self.frame_duration:
            self.timer = 0.0
            self.current_frame = (self.current_frame + 1) % len(self.textures)
            self.texture = self.textures[self.current_frame]

class MainMenu(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_list = arcade.SpriteList()
        self.animated_bg = None

    def on_show_view(self):
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        frames = []
        for number in range(1,12+1):
            texture = arcade.load_texture(f'images/MainMenu/{number}.png')
            frames.append(texture)
        self.animated_bg = AnimatedBackground(frames, frame_duration=2, scale=1.0)
        self.animated_bg.center_x = self.window.width / 2
        self.animated_bg.center_y = self.window.height / 2
        self.background_list.append(self.animated_bg)

def on_update(self, delta_time):
    if self.animated_bg is not None:
        self.animated_bg.update_animation(delta_time)

    def on_draw(self):
        self.clear()
        self.background_list.draw()
    
class SettingMenu(arcade.View):
    pass