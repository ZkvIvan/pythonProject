import math, random, arcade

FONT = "Cyrillic Pixel-7"
SLOT_W, SLOT_H = 120, 170
AMBIENT = {
    "fire": (14, [(255, 120, 30), (255, 190, 60), (255, 80, 20)], (-14, 14), (55, 120), (3, 5), (0.5, 0.95), 30),
    "poison": (8, [(110, 220, 80), (70, 180, 60)], (-10, 10), (22, 55), (3, 4), (0.9, 1.5), 0),
    "curse": (7, [(160, 70, 210), (110, 40, 160)], (-12, 12), (15, 45), (3, 4), (0.9, 1.4), 0),
    "rebirth": (7, [(255, 210, 90), (255, 150, 40)], (-14, 14), (35, 80), (2, 4), (0.6, 1.1), 10),
    "flying": (5, [(205, 215, 235)], (-30, 30), (-15, 25), (2, 3), (0.8, 1.3), 0),
}

def _make_color(r, g, b, a):
    try:
        from arcade.types import Color
        return Color(r, g, b, a)
    except Exception: return None

def draw_tinted(tex, rect, alpha=255):
    if alpha >= 255: arcade.draw_texture_rect(tex, rect); return
    tint = _make_color(255, 255, 255, alpha)
    if tint:
        try: arcade.draw_texture_rect(tex, rect, color=tint); return
        except Exception: pass
    arcade.draw_texture_rect(tex, rect)

class VFX:
    def __init__(self, view):
        self.view = view
        self.particles, self.rings, self.texts, self.ghosts = [], [], [], []
        self.recoils, self.flashes = {}, []
        self.banner = self.glow = self.over_t = None
        self.hero = {"player": 0.0, "enemy": 0.0}
        self.shake_amt = self._dust_acc = self._over_acc = 0.0

    @property
    def s(self): return self.view.lay.s

    def burst(self, x, y, colors, count, speed, size=(2, 4), life=(0.3, 0.6), gravity=0.0, drag=0.0, angle=None, spread=math.tau, shrink=True, layer=1, amax=255):
        s = self.s
        for _ in range(count):
            if len(self.particles) >= 450: break
            a = random.uniform(0, math.tau) if angle is None else angle + random.uniform(-spread / 2, spread / 2)
            sp = speed * s * random.uniform(0.35, 1.0)
            self.particles.append([x, y, math.cos(a) * sp, math.sin(a) * sp, gravity * s, drag, random.uniform(*life), random.uniform(*life), max(1.0, random.uniform(*size) * s), random.choice(colors), shrink, layer, amax])

    def ring(self, x, y, color, r0, r1, life=0.35, width=3): self.rings.append([x, y, r0 * self.s, r1 * self.s, 0.0, life, color, width])

    def float_text(self, x, y, text, color, size=28, life=0.9):
        s = self.s
        self.texts.append([arcade.Text(text, x, y, (*color, 255), size * s, font_name=FONT, anchor_x="center", anchor_y="center"),
                           arcade.Text(text, x + 2 * s, y - 2 * s, (0, 0, 0, 255), size * s, font_name=FONT, anchor_x="center", anchor_y="center"),
                           x, y, 85 * s, 0.0, life, color])

    def flash(self, color, alpha, life=0.25): self.flashes = [f for f in self.flashes if f[0] != color] + [[color, alpha, 0.0, life]]
    def shake(self, amount): self.shake_amt = max(self.shake_amt, amount * self.s)
    def shake_offset(self): return (random.uniform(-a, a), random.uniform(-a, a)) if (a := self.shake_amt) >= 0.3 else (0.0, 0.0)
    def show_banner(self, text, color=(255, 255, 255), total=1.5, style="turn"): self.banner = [text, 0.0, total, color, style]
    def column_glow(self, col): self.glow = [col, 0.0, 0.55]
    def kick(self, card, direction, amount=16): self.recoils[card] = [direction * amount * self.s, 0.0]
    def start_game_over(self, win): self.over_t, self.over_win = 0.0, win

    def place(self, x, y, enemy=False):
        if enemy: self.ring(x, y, (170, 70, 220), 25, 95, 0.4, 4); self.burst(x, y, [(90, 40, 130), (60, 30, 90), (150, 70, 200)], 18, 120, (3, 6), (0.4, 0.8), -30, 2.5); self.shake(2)
        else: self.ring(x, y, (230, 200, 110), 25, 90, 0.35, 3); self.burst(x, y, [(200, 200, 205), (150, 150, 160), (230, 200, 110)], 14, 150, (2, 4), (0.3, 0.55), 0, 4); self.shake(1.5)

    def select(self, x, y):
        self.ring(x, y, (255, 255, 255), 40, 72, 0.25, 2)
        self.burst(x, y + 60 * self.s, [(255, 255, 255), (255, 225, 140)], 6, 70, (2, 3), (0.3, 0.5), -20, 0, math.pi / 2, 1.2)

    def clash(self, p, e, p_dmg=None, e_dmg=None):
        mx, my = (p.center_x + e.center_x) / 2, (p.center_y + e.center_y) / 2
        self.burst(mx, my, [(255, 255, 255), (255, 200, 80), (255, 110, 40)], 22, 260, (2, 5), (0.2, 0.5), 0, 3)
        self.ring(mx, my, (255, 220, 150), 15, 85, 0.3, 3)
        if p_dmg is not None: self.float_text(p.center_x, p.center_y + 20 * self.s, f"-{e_dmg}", (255, 70, 70))
        if e_dmg is not None: self.float_text(e.center_x, e.center_y + 20 * self.s, f"-{p_dmg}", (255, 70, 70))
        self.kick(p, -1); self.kick(e, +1); self.shake(3 + 0.7 * ((p_dmg or 0) + (e_dmg or 0)))

    def hero_hit(self, side, dmg):
        x, y = self.view.lay.enemy_hero if side == "enemy" else self.view.lay.player_hero
        self.hero[side] = 0.45
        self.burst(x, y, [(255, 60, 40), (200, 20, 20), (255, 140, 90)], 26, 280, (3, 6), (0.35, 0.8), -160, 2)
        self.ring(x, y, (255, 70, 50), 30, 140, 0.4, 4)
        self.float_text(x, y + 40 * self.s, f"-{dmg}", (255, 60, 60), 40, 1.1)
        self.flash((200, 20, 20), 45, 0.3); self.shake(min(18, 4 + dmg * 1.6))

    def card_death(self, card):
        self.ghosts.append([card.texture, card.center_x, card.center_y, card.width, card.height, 0.0, 0.7])
        self.burst(card.center_x, card.center_y, [(60, 55, 60), (110, 100, 105), (170, 40, 40)], 28, 150, (3, 6), (0.5, 1.0), -80, 1.5)
        self.ring(card.center_x, card.center_y, (170, 40, 40), 30, 100, 0.45, 3)

    def energy_spark(self, ratio=1.0):
        bx, by, bw, bh = self.view.lay.p_en_bar
        self.burst(bx + bw * ratio, by + bh / 2, [(0, 230, 255), (180, 250, 255)], 10, 110, (2, 4), (0.3, 0.6), 0, 2)

    def energy_refill(self):
        bx, by, bw, bh = self.view.lay.p_en_bar
        for i in range(3): self.burst(bx + bw * (i + 0.5) / 3, by + bh / 2, [(0, 230, 255), (180, 250, 255)], 8, 100, (2, 4), (0.3, 0.6), -30, 0, math.pi / 2, 2.0)

    def update(self, dt):
        dt, s, L = min(dt, 0.05), self.s, self.view.lay
        for p in self.particles:
            p[0] += p[2] * dt; p[1] += p[3] * dt; p[3] += p[4] * dt; p[6] -= dt
            if p[5]: k = max(0.0, 1.0 - p[5] * dt); p[2] *= k; p[3] *= k
        self.particles = [p for p in self.particles if p[6] > 0]
        for r in self.rings: r[4] += dt
        self.rings = [r for r in self.rings if r[4] < r[5]]
        for g in self.ghosts: g[5] += dt
        self.ghosts = [g for g in self.ghosts if g[5] < g[6]]
        for f in self.flashes: f[2] += dt
        self.flashes = [f for f in self.flashes if f[2] < f[3]]
        for t in self.texts:
            t[5] += dt; t[3] += t[4] * dt; t[4] *= math.exp(-2.2 * dt)
            a = int(255 * max(0.0, 1.0 - (t[5] / t[6]) ** 3))
            if a < 5: continue
            t[0].x, t[0].y, t[0].color = t[2], t[3], (*t[7], a)
            t[1].x, t[1].y, t[1].color = t[2] + 2 * s, t[3] - 2 * s, (0, 0, 0, a)
        self.texts = [t for t in self.texts if t[5] < t[6]]
        for card in list(self.recoils):
            off, age = self.recoils[card]; age += dt; cur = off * math.exp(-9 * age)
            if abs(cur) < 0.5: card.fx_x = card.fx_y = 0.0; del self.recoils[card]
            else: card.fx_y, card.fx_x = cur, random.uniform(-1, 1) * abs(cur) * 0.25; self.recoils[card][1] = age
        for k in self.hero: self.hero[k] = max(0.0, self.hero[k] - dt)
        self.shake_amt *= math.exp(-9 * dt)
        if self.banner:
            self.banner[1] += dt
            if self.banner[1] >= self.banner[2]: self.banner = None
        if self.glow:
            self.glow[1] += dt
            if self.glow[1] >= self.glow[2]: self.glow = None
        self._emit_ambient(dt, L)
        if self.over_t is not None:
            self.over_t += dt; self._over_acc += dt * 45
            while self._over_acc >= 1:
                self._over_acc -= 1; x = random.uniform(0, L.w)
                if self.over_win:
                    self.burst(x, 0, [(255, 215, 90), (255, 240, 170), (255, 160, 40)], 1, 0, (2, 4), (1.0, 1.8), 0, 0, None, math.tau, True, 1)
                    if self.particles: self.particles[-1][2], self.particles[-1][3], self.particles[-1][4] = random.uniform(-30, 30), random.uniform(220, 420) * L.s, -60
                else:
                    self.burst(x, L.h, [(90, 85, 90), (140, 130, 135), (170, 40, 40)], 1, 0, (2, 4), (1.2, 2.0), 0, 0, None, math.tau, False, 1)
                    if self.particles: self.particles[-1][2], self.particles[-1][3], self.particles[-1][4] = random.uniform(-25, 25), -random.uniform(60, 160) * L.s, 0

    def _emit_ambient(self, dt, L):
        s = L.s
        self._dust_acc += dt * 6
        while self._dust_acc >= 1:
            self._dust_acc -= 1
            if len(self.particles) < 450: self.particles.append([random.uniform(L.tx0, L.tx1), random.uniform(L.mid_y0, L.mid_y1), random.uniform(-8, 8) * s, random.uniform(3, 14) * s, 0, 0, 5, random.uniform(5, 9), max(1.0, random.uniform(2, 3) * s), (215, 215, 225), False, 0, 75])
        if self.view.phase == "over": return
        for card in self.view.card_sprite_list:
            if card.hp <= 0: continue
            kws = getattr(card, "_fx_kw", None)
            if kws is None:
                kws = card._fx_kw = [k for k in self.view.cards_by_id.get(card.texture_name, {}).get("keywords", []) if k in AMBIENT]
                card._fx_acc = {}
            for kw in kws:
                cfg = AMBIENT[kw]
                acc = card._fx_acc.get(kw, 0.0) + dt * cfg[0]
                while acc >= 1:
                    acc -= 1
                    if len(self.particles) < 450: self.particles.append([card.center_x + random.uniform(-0.38, 0.38) * card.width, card.center_y + random.uniform(-0.25, 0.4) * card.height, random.uniform(*cfg[2]) * s, random.uniform(*cfg[3]) * s, cfg[6] * s, 0, random.uniform(*cfg[5]), random.uniform(*cfg[5]), max(1.0, random.uniform(*cfg[4]) * s), random.choice(cfg[1]), True, 1, 255])
                card._fx_acc[kw] = acc

    def _draw_particles(self, layer):
        groups = {}
        for p in self.particles:
            if p[11] != layer: continue
            a = p[6] / p[7]; f = math.sin(math.pi * a) if layer == 0 else min(1.0, a * 1.6)
            alpha = int(p[12] * max(0.0, f))
            if alpha < 8: continue
            ab = min(255, (alpha // 64) * 64 + 63); size = max(1, round(p[8] * (a if p[10] else 1.0) + 0.3))
            groups.setdefault((p[9], ab, size), []).append((p[0], p[1]))
        for (color, alpha, size), pts in groups.items(): arcade.draw_points(pts, (*color, alpha), size)

    def draw_under(self):
        L, s = self.view.lay, self.view.lay.s
        if self.glow:
            col, age, life = self.glow; f = 1.0 - age / life; cx = L.slot_x0 + (col - 2) * L.slot_step
            w, y0, y1 = SLOT_W * s + 24 * s, L.player_row_y - SLOT_H * s / 2 - 12 * s, L.enemy_row_y + SLOT_H * s / 2 + 12 * s
            arcade.draw_lbwh_rectangle_filled(cx - w / 2, y0, w, y1 - y0, (255, 210, 90, int(60 * f)))
            arcade.draw_lbwh_rectangle_outline(cx - w / 2, y0, w, y1 - y0, (255, 220, 120, int(200 * f)), 3)
        self._draw_particles(0)

    def draw_world(self):
        for tex, x, y, w, h, age, life in self.ghosts:
            f = age / life; alpha = int(255 * (1 - f) ** 1.5); sc = 1.0 + 0.12 * f
            draw_tinted(tex, arcade.LBWH(x - w * sc / 2, y - h * sc / 2 + 40 * self.s * f, w * sc, h * sc), alpha)
        self._draw_particles(1)
        for x, y, r0, r1, age, life, color, width in self.rings:
            f = age / life; r = r0 + (r1 - r0) * (1 - (1 - f) ** 2)
            arcade.draw_circle_outline(x, y, r, (*color, int(255 * (1 - f))), width * max(1.0, self.s))
        for t in self.texts: t[1].draw(); t[0].draw()

    def draw_overlay(self):
        L, s = self.view.lay, self.view.lay.s
        for rgb, alpha, age, life in self.flashes: arcade.draw_lbwh_rectangle_filled(0, 0, L.w, L.h, (*rgb, int(alpha * (1 - age / life))))
        if self.banner:
            text, age, total, rgb, style = self.banner; tin, tout = (0.45, 0.5) if style == "fight" else (0.3, 0.35)
            if age < tin: k = age / tin; ease = 1 - (1 - k) ** 3; fade, off = k, -(1 - ease) * L.w * 0.65
            elif age > total - tout: k = (age - (total - tout)) / tout; fade, off = 1 - k, k * L.w * 0.65
            else: fade, off = 1.0, 0.0
            if style == "fight":
                arcade.draw_lbwh_rectangle_filled(0, 0, L.w, L.h, (0, 0, 0, int(150 * fade)))
                pulse = (1.0 + 0.06 * math.sin((age - tin) * 9)) if tin < age < total - tout else 1.0
                bh = 200 * s * pulse
                arcade.draw_lbwh_rectangle_filled(0, L.mid - bh / 2, L.w, bh, (130, 10, 10, int(235 * fade)))
                arcade.draw_lbwh_rectangle_filled(0, L.mid - bh / 2, L.w, 5 * s, (*rgb, int(235 * fade)))
                arcade.draw_lbwh_rectangle_filled(0, L.mid + bh / 2 - 5 * s, L.w, 5 * s, (*rgb, int(235 * fade)))
                arcade.draw_text(text, L.w / 2 + off, L.mid, (255, 255, 255, int(255 * fade)), int(140 * s * pulse), font_name=FONT, anchor_x="center", anchor_y="center")
            else:
                band_h = 110 * s
                arcade.draw_lbwh_rectangle_filled(0, L.mid - band_h / 2, L.w, band_h, (0, 0, 0, int(170 * fade)))
                arcade.draw_lbwh_rectangle_filled(0, L.mid + band_h / 2 - 3, L.w, 3, (*rgb, int(220 * fade)))
                arcade.draw_lbwh_rectangle_filled(0, L.mid - band_h / 2, L.w, 3, (*rgb, int(220 * fade)))
                arcade.draw_text(text, L.w / 2 + off, L.mid, (*rgb, int(255 * fade)), int(56 * s), font_name=FONT, anchor_x="center", anchor_y="center")
        if self.over_t is not None:
            a = min(1.0, self.over_t / 0.8); k = min(1.0, self.over_t * 2.5); scale = 0.6 + 0.4 * (1 - (1 - k) ** 3); win = self.over_win
            arcade.draw_lbwh_rectangle_filled(0, 0, L.w, L.h, (0, 0, 0, int(190 * a)))
            arcade.draw_text("ПОБЕДА!" if win else "ПОРАЖЕНИЕ", L.w / 2, L.h / 2, (255, 215, 0, int(255 * k)) if win else (200, 40, 40, int(255 * k)), 72 * s * scale, font_name=FONT, anchor_x="center", anchor_y="center")
            arcade.draw_text("[ENTER] — продолжить" if win else "[ENTER] — в меню", L.w / 2, L.h / 2 - 120 * s, (200, 200, 200, int(180 * k)), 22 * s, font_name=FONT, anchor_x="center", anchor_y="center")
            self._draw_particles(1)