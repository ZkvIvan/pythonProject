import arcade
from utils import FONT_TITLE, FONT_UI

class EndGameView(arcade.View):
    def __init__(self, player_name, cards_collected):
        super().__init__()
        self.player_name = player_name
        self.cards_collected = cards_collected
        self.time = 0.0
        self.ending_text = (
            "Ты разорвал колоду.\n\n"
            "Стол рассыпался в прах. Ночные кошмары, Ткач и его тени — всё обратилось в ничто.\n"
            "Ты больше не слышишь шепота карт. Но ты слышишь тишину.\n"
            "Мир не спасен. Он просто стерт. И в этом забвении нет ни света, ни тьмы.\n\n"
            "Ты сделал свой выбор. Теперь спи."
        )

    def on_draw(self):
        self.clear()
        w, h = self.window.width, self.window.height
        s = h / 1080
        arcade.draw_lbwh_rectangle_filled(0, 0, w, h, (0, 0, 0))
        alpha = min(255, int(self.time * 20))
        if alpha > 5:
            arcade.draw_text(self.ending_text, w/2, h/2 + 50*s, (120, 120, 120, alpha), 24*s, font_name=FONT_UI, anchor_x="center", align="center", width=800*s)
            if self.time > 5:
                arcade.draw_text(f"Жнец: {self.player_name}\nОсколков душ: {self.cards_collected}\n\n[ESC] — сгинуть", w/2, h/2 - 250*s, (60, 60, 60, alpha), 16*s, font_name=FONT_TITLE, anchor_x="center")

    def on_update(self, delta_time):
        self.time += delta_time

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            from MainMenu import MainMenu
            self.window.show_view(MainMenu())