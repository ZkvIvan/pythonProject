# ============================================================
# vfx.py — визуальные эффекты боя.
#   частицы · кольца-ударные волны · всплывающие числа · призраки погибших карт
#   отдача карт · баннеры хода · вспышки · тряска экрана · экран победы/поражения
# Скорость берётся из настройки animation_speed (GameView передаёт dt уже умноженным).
# ============================================================

import math
import random

import arcade

FONT = "Cyrillic Pixel-7"
SLOT_W, SLOT_H = 120, 170

# Постоянные эффекты на картах стола по ключевым словам из cards.json
AMBIENT = {
    "fire":    dict(rate=14, colors=[(255, 120, 30), (255, 190, 60), (255, 80, 20)],
                    vx=(-14, 14), vy=(55, 120), size=(3, 5), life=(0.5, 0.95), gy=30),
    "poison":  dict(rate=8, colors=[(110, 220, 80), (70, 180, 60)],
                    vx=(-10, 10), vy=(22, 55), size=(3, 4), life=(0.9, 1.5), gy=0),
    "curse":   dict(rate=7, colors=[(160, 70, 210), (110, 40, 160)],
                    vx=(-12, 12), vy=(15, 45), size=(3, 4), life=(0.9, 1.4), gy=0),
    "rebirth": dict(rate=7, colors=[(255, 210, 90), (255, 150, 40)],
                    vx=(-14, 14), vy=(35, 80), size=(2, 4), life=(0.6, 1.1), gy=10),
    "flying":  dict(rate=5, colors=[(205, 215, 235)],
                    vx=(-30, 30), vy=(-15, 25), size=(2, 3), life=(0.8, 1.3), gy=0),
}


class _P:
    __slots__ = ("x", "y", "vx", "vy", "gy", "drag", "life", "max", "size",
                 "color", "shrink", "amax", "layer")


class VFX:
    MAX_PARTICLES = 450

    def __init__(self, view):
        self.view = view
        self.particles = []
        self.rings = []         # [x, y, r0, r1, age, life, color, width]
        self.texts = []         # [text, shadow, x, y, vy, age, life, rgb]
        self.ghosts = []        # [texture, x, y, w, h, age, life]
        self.recoils = {}       # card -> [offset, age]
        self.flashes = []       # [rgb, alpha, age, life]
        self.banner = None      # [text, age, total, rgb]
        self.glow = None        # [col, age, life]
        self.hero = {"player": 0.0, "enemy": 0.0}   # таймеры «герой получил урон»
        self.shake_amt = 0.0
        self.over_t = None
        self.over_win = True
        self._dust_acc = 0.0
        self._over_acc = 0.0

    @property
    def s(self):
        return self.view.lay.s

    # =====================================================================
    # СОЗДАНИЕ ЭФФЕКТОВ
    # =====================================================================
    def burst(self, x, y, colors, count, speed, size=(2, 4), life=(0.3, 0.6),
              gravity=0.0, drag=0.0, angle=None, spread=math.tau, shrink=True,
              layer=1, amax=255):
        s = self.s
        for _ in range(count):
            if len(self.particles) >= self.MAX_PARTICLES:
                return
            a = random.uniform(0, math.tau) if angle is None else angle + random.uniform(-spread / 2, spread / 2)
            sp = speed * s * random.uniform(0.35, 1.0)
            p = _P()
            p.x, p.y = x, y
            p.vx, p.vy = math.cos(a) * sp, math.sin(a) * sp
            p.gy, p.drag = gravity * s, drag
            p.life = p.max = random.uniform(*life)
            p.size = max(1.0, random.uniform(*size) * s)
            p.color = random.choice(colors)
            p.shrink, p.layer, p.amax = shrink, layer, amax
            self.particles.append(p)

    def ring(self, x, y, color, r0, r1, life=0.35, width=3):
        s = self.s
        self.rings.append([x, y, r0 * s, r1 * s, 0.0, life, color, width])

    def float_text(self, x, y, text, color, size=28, life=0.9):
        s = self.s
        t = arcade.Text(text, x, y, (*color, 255), size * s, font_name=FONT,
                        anchor_x="center", anchor_y="center")
        sh = arcade.Text(text, x + 2 * s, y - 2 * s, (0, 0, 0, 255), size * s, font_name=FONT,
                         anchor_x="center", anchor_y="center")
        self.texts.append([t, sh, x, y, 85 * s, 0.0, life, color])

    def flash(self, color, alpha, life=0.25):
        self.flashes = [f for f in self.flashes if f[0] != color]   # одинаковые вспышки не копятся
        self.flashes.append([color, alpha, 0.0, life])

    def shake(self, amount):
        self.shake_amt = max(self.shake_amt, amount * self.s)

    def shake_offset(self):
        a = self.shake_amt
        if a < 0.3:
            return 0.0, 0.0
        return random.uniform(-a, a), random.uniform(-a, a)

    def show_banner(self, text, color=(255, 255, 255), total=1.5):
        s = self.s
        t = arcade.Text(text, 0, 0, (*color, 255), 56 * s, font_name=FONT,
                        anchor_x="center", anchor_y="center")
        self.banner = [t, 0.0, total, color]

    def column_glow(self, col):
        self.glow = [col, 0.0, 0.55]

    def kick(self, card, direction, amount=16):
        """Отдача карты при ударе (direction: +1 вверх, -1 вниз)."""
        self.recoils[card] = [direction * amount * self.s, 0.0]

    def start_game_over(self, win):
        self.over_t, self.over_win = 0.0, win

    # ---- готовые композиции ------------------------------------------------
    def place(self, x, y, enemy=False):
        if enemy:
            self.ring(x, y, (170, 70, 220), 25, 95, 0.4, 4)
            self.burst(x, y, [(90, 40, 130), (60, 30, 90), (150, 70, 200)], 18, 120,
                       size=(3, 6), life=(0.4, 0.8), gravity=-30, drag=2.5)
            self.shake(2)
        else:
            self.ring(x, y, (230, 200, 110), 25, 90, 0.35, 3)
            self.burst(x, y, [(200, 200, 205), (150, 150, 160), (230, 200, 110)], 14, 150,
                       size=(2, 4), life=(0.3, 0.55), drag=4)
            self.shake(1.5)

    def select(self, x, y):
        self.ring(x, y, (255, 255, 255), 40, 72, 0.25, 2)
        self.burst(x, y + 60 * self.s, [(255, 255, 255), (255, 225, 140)], 6, 70,
                   size=(2, 3), life=(0.3, 0.5), angle=math.pi / 2, spread=1.2, gravity=-20)

    def clash(self, p, e):
        s = self.s
        mx, my = (p.center_x + e.center_x) / 2, (p.center_y + e.center_y) / 2
        self.burst(mx, my, [(255, 255, 255), (255, 200, 80), (255, 110, 40)], 22, 260,
                   size=(2, 5), life=(0.2, 0.5), drag=3)
        self.ring(mx, my, (255, 220, 150), 15, 85, 0.3, 3)
        self.float_text(p.center_x, p.center_y + 20 * s, f"-{e.strength}", (255, 70, 70))
        self.float_text(e.center_x, e.center_y + 20 * s, f"-{p.strength}", (255, 70, 70))
        self.kick(p, -1)
        self.kick(e, +1)
        self.shake(3 + 0.7 * (p.strength + e.strength))

    def hero_hit(self, side, dmg):
        x, y = self.view.lay.enemy_hero if side == "enemy" else self.view.lay.player_hero
        self.hero[side] = 0.45
        self.burst(x, y, [(255, 60, 40), (200, 20, 20), (255, 140, 90)], 26, 280,
                   size=(3, 6), life=(0.35, 0.8), gravity=-160, drag=2)
        self.ring(x, y, (255, 70, 50), 30, 140, 0.4, 4)
        self.float_text(x, y + 40 * self.s, f"-{dmg}", (255, 60, 60), size=40, life=1.1)
        self.flash((200, 20, 20), 45, 0.3)
        self.shake(min(18, 4 + dmg * 1.6))

    def card_death(self, card):
        s = self.s
        self.ghosts.append([card.texture, card.center_x, card.center_y,
                            card.width, card.height, 0.0, 0.7])
        self.burst(card.center_x, card.center_y, [(60, 55, 60), (110, 100, 105), (170, 40, 40)],
                   28, 150, size=(3, 6), life=(0.5, 1.0), gravity=-80, drag=1.5)
        self.ring(card.center_x, card.center_y, (170, 40, 40), 30, 100, 0.45, 3)

    def energy_spark(self, ratio=1.0):
        bx, by, bw, bh = self.view.lay.p_en_bar
        self.burst(bx + bw * ratio, by + bh / 2, [(0, 230, 255), (180, 250, 255)], 10, 110,
                   size=(2, 4), life=(0.3, 0.6), drag=2)

    def energy_refill(self):
        bx, by, bw, bh = self.view.lay.p_en_bar
        for i in range(3):
            self.burst(bx + bw * (i + 0.5) / 3, by + bh / 2, [(0, 230, 255), (180, 250, 255)],
                       8, 100, size=(2, 4), life=(0.3, 0.6), angle=math.pi / 2, spread=2.0, gravity=-30)

    # =====================================================================
    # ОБНОВЛЕНИЕ
    # =====================================================================
    def update(self, dt):
        dt = min(dt, 0.05)
        s = self.s
        L = self.view.lay

        # частицы
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vy += p.gy * dt
            if p.drag:
                k = max(0.0, 1.0 - p.drag * dt)
                p.vx *= k
                p.vy *= k
            alive.append(p)
        self.particles = alive

        # кольца, тексты, призраки, вспышки
        self.rings = [r for r in self.rings if self._age(r, 4, dt) < r[5]]
        for ghost in self.ghosts:
            ghost[5] += dt
        self.ghosts = [g for g in self.ghosts if g[5] < g[6]]
        for f in self.flashes:
            f[2] += dt
        self.flashes = [f for f in self.flashes if f[2] < f[3]]

        keep = []
        for item in self.texts:
            item[5] += dt
            item[3] += item[4] * dt
            item[4] *= math.exp(-2.2 * dt)
            fade = 1.0 - (item[5] / item[6]) ** 3
            if fade <= 0.02:
                continue
            a = int(255 * fade)
            t, sh, x, y, _, _, _, rgb = item
            t.x, t.y, t.color = x, y, (*rgb, a)
            sh.x, sh.y, sh.color = x + 2 * s, y - 2 * s, (0, 0, 0, a)
            keep.append(item)
        self.texts = keep

        # отдача карт
        for card in list(self.recoils):
            off, age = self.recoils[card]
            age += dt
            cur = off * math.exp(-9 * age)
            if abs(cur) < 0.5:
                card.fx_x = card.fx_y = 0.0
                del self.recoils[card]
                continue
            card.fx_y = cur
            card.fx_x = random.uniform(-1, 1) * abs(cur) * 0.25
            self.recoils[card][1] = age

        # таймеры
        for k in self.hero:
            self.hero[k] = max(0.0, self.hero[k] - dt)
        self.shake_amt *= math.exp(-9 * dt)
        if self.banner:
            self.banner[1] += dt
            if self.banner[1] >= self.banner[2]:
                self.banner = None
        if self.glow:
            self.glow[1] += dt
            if self.glow[1] >= self.glow[2]:
                self.glow = None

        self._emit_ambient(dt, L)
        self._emit_game_over(dt, L)

    @staticmethod
    def _age(entry, idx, dt):
        entry[idx] += dt
        return entry[idx]

    def _emit_ambient(self, dt, L):
        s = L.s
        # пылинки над столом
        self._dust_acc += dt * 6
        while self._dust_acc >= 1:
            self._dust_acc -= 1
            if len(self.particles) < self.MAX_PARTICLES:
                p = _P()
                p.x = random.uniform(L.tx0, L.tx1)
                p.y = random.uniform(L.mid_y0, L.mid_y1)
                p.vx, p.vy = random.uniform(-8, 8) * s, random.uniform(3, 14) * s
                p.gy = p.drag = 0
                p.life = p.max = random.uniform(5, 9)
                p.size = max(1.0, random.uniform(2, 3) * s)
                p.color, p.shrink, p.layer, p.amax = (215, 215, 225), False, 0, 75
                self.particles.append(p)

        if self.view.phase == "over":
            return
        for card in self.view.card_sprite_list:
            if card.hp <= 0:
                continue
            kws = getattr(card, "_fx_kw", None)
            if kws is None:
                info = self.view.cards_by_id.get(card.texture_name, {})
                kws = card._fx_kw = [k for k in info.get("keywords", []) if k in AMBIENT]
                card._fx_acc = {}
            for kw in kws:
                cfg = AMBIENT[kw]
                acc = card._fx_acc.get(kw, 0.0) + dt * cfg["rate"]
                while acc >= 1:
                    acc -= 1
                    if len(self.particles) >= self.MAX_PARTICLES:
                        break
                    p = _P()
                    p.x = card.center_x + random.uniform(-0.38, 0.38) * card.width
                    p.y = card.center_y + random.uniform(-0.25, 0.4) * card.height
                    p.vx, p.vy = random.uniform(*cfg["vx"]) * s, random.uniform(*cfg["vy"]) * s
                    p.gy, p.drag = cfg["gy"] * s, 0
                    p.life = p.max = random.uniform(*cfg["life"])
                    p.size = max(1.0, random.uniform(*cfg["size"]) * s)
                    p.color, p.shrink, p.layer, p.amax = random.choice(cfg["colors"]), True, 1, 255
                    self.particles.append(p)
                card._fx_acc[kw] = acc

    def _emit_game_over(self, dt, L):
        if self.over_t is None:
            return
        self.over_t += dt
        self._over_acc += dt * 45
        while self._over_acc >= 1:
            self._over_acc -= 1
            x = random.uniform(0, L.w)
            if self.over_win:   # золотые искры снизу вверх
                self.burst(x, 0, [(255, 215, 90), (255, 240, 170), (255, 160, 40)], 1, 0,
                           size=(2, 4), life=(1.0, 1.8), shrink=True, layer=1)
                p = self.particles[-1] if self.particles else None
                if p:
                    p.vx, p.vy, p.gy = random.uniform(-30, 30), random.uniform(220, 420) * L.s, -60
            else:               # пепел сверху вниз
                self.burst(x, L.h, [(90, 85, 90), (140, 130, 135), (170, 40, 40)], 1, 0,
                           size=(2, 4), life=(1.2, 2.0), shrink=False, layer=1)
                p = self.particles[-1] if self.particles else None
                if p:
                    p.vx, p.vy, p.gy = random.uniform(-25, 25), -random.uniform(60, 160) * L.s, 0

    # =====================================================================
    # ОТРИСОВКА
    # =====================================================================
    def _draw_particles(self, layer):
        groups = {}
        for p in self.particles:
            if p.layer != layer:
                continue
            a = p.life / p.max
            f = math.sin(math.pi * a) if layer == 0 else min(1.0, a * 1.6)
            alpha = int(p.amax * max(0.0, f))
            if alpha < 8:
                continue
            ab = min(255, (alpha // 64) * 64 + 63)             # 4 уровня прозрачности
            size = max(1, round(p.size * (a if p.shrink else 1.0) + 0.3))
            groups.setdefault((p.color, ab, size), []).append((p.x, p.y))
        for (color, alpha, size), pts in groups.items():
            arcade.draw_points(pts, (*color, alpha), size)

    def draw_under(self):
        """Под картами: свечение колонки, пылинки."""
        L = self.view.lay
        s = L.s
        if self.glow:
            col, age, life = self.glow
            f = 1.0 - age / life
            cx = L.slot_x0 + (col - 2) * L.slot_step
            w = SLOT_W * s + 24 * s
            y0 = L.player_row_y - SLOT_H * s / 2 - 12 * s
            y1 = L.enemy_row_y + SLOT_H * s / 2 + 12 * s
            arcade.draw_lbwh_rectangle_filled(cx - w / 2, y0, w, y1 - y0, (255, 210, 90, int(60 * f)))
            arcade.draw_lbwh_rectangle_outline(cx - w / 2, y0, w, y1 - y0, (255, 220, 120, int(200 * f)), 3)
        self._draw_particles(0)

    def draw_world(self):
        """Поверх всего интерфейса: частицы, кольца, призраки, числа."""
        for g in self.ghosts:
            tex, x, y, w, h, age, life = g
            f = age / life
            alpha = int(255 * (1 - f) ** 1.5)
            rise = 40 * self.s * f
            sc = 1.0 + 0.12 * f
            rect = arcade.LBWH(x - w * sc / 2, y - h * sc / 2 + rise, w * sc, h * sc)
            try:
                arcade.draw_texture_rect(tex, rect, color=(255, 255, 255, alpha))
            except TypeError:                       # старая версия arcade без color=
                arcade.draw_texture_rect(tex, rect)
        self._draw_particles(1)
        for x, y, r0, r1, age, life, color, width in self.rings:
            f = age / life
            r = r0 + (r1 - r0) * (1 - (1 - f) ** 2)
            arcade.draw_circle_outline(x, y, r, (*color, int(255 * (1 - f))), width * max(1.0, self.s))
        for item in self.texts:
            item[1].draw()
            item[0].draw()

    def draw_overlay(self):
        """Самый верх: вспышки, баннер хода, экран победы/поражения."""
        L = self.view.lay
        s = L.s
        for rgb, alpha, age, life in self.flashes:
            arcade.draw_lbwh_rectangle_filled(0, 0, L.w, L.h, (*rgb, int(alpha * (1 - age / life))))

        if self.banner:
            t, age, total, rgb = self.banner
            tin, tout = 0.3, 0.35
            if age < tin:
                k = age / tin
                ease, fade = 1 - (1 - k) ** 3, k
                off = -(1 - ease) * L.w * 0.25
            elif age > total - tout:
                k = (age - (total - tout)) / tout
                fade, off = 1 - k, k * L.w * 0.25
            else:
                fade, off = 1.0, 0.0
            band_h = 110 * s
            cy = L.mid
            arcade.draw_lbwh_rectangle_filled(0, cy - band_h / 2, L.w, band_h, (0, 0, 0, int(170 * fade)))
            arcade.draw_lbwh_rectangle_filled(0, cy + band_h / 2 - 3, L.w, 3, (*rgb, int(220 * fade)))
            arcade.draw_lbwh_rectangle_filled(0, cy - band_h / 2, L.w, 3, (*rgb, int(220 * fade)))
            t.x, t.y, t.color = L.w / 2 + off, cy, (*rgb, int(255 * fade))
            t.draw()

        if self.over_t is not None:
            a = min(1.0, self.over_t / 0.8)
            arcade.draw_lbwh_rectangle_filled(0, 0, L.w, L.h, (0, 0, 0, int(190 * a)))
            k = min(1.0, self.over_t * 2.5)
            scale = 0.6 + 0.4 * (1 - (1 - k) ** 3)
            win = self.over_win
            arcade.draw_text("ПОБЕДА!" if win else "ПОРАЖЕНИЕ", L.w / 2, L.h / 2,
                             (255, 215, 0, int(255 * k)) if win else (200, 40, 40, int(255 * k)),
                             72 * s * scale, font_name=FONT, anchor_x="center", anchor_y="center")
            self._draw_particles(1)