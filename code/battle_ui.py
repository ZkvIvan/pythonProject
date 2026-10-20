import math, random, arcade
from arcade import gl

FONT = "Cyrillic Pixel-7"
CARD_W, CARD_H, SLOT_W, SLOT_H = 117, 168, 120, 170

def draw_ui(view):
    L, s, w, h = view.lay, view.lay.s, view.window.width, view.window.height
    
    pts, y, flip = [], L.mid_y0 + 30 * s, 1
    while y < L.mid_y1 - 30 * s:
        pts.append((L.wavy_x + flip * 6 * s, y)); y += 18 * s; flip = -flip
    pts.append((L.wavy_x + flip * 6 * s, L.mid_y1 - 30 * s))
    arcade.draw_line_strip(pts, (90, 90, 100), 3)

    cx, cy, radius = L.turn_cx, L.turn_cy, L.turn_r
    if view.phase == "player":
        pulse = math.sin(view.time * 3)
        arcade.draw_circle_filled(cx, cy, radius + (pulse * 10 * s), (255, 200, 0, int(100 + pulse * 50)))
        arcade.draw_circle_outline(cx, cy, radius, (255, 255, 255, 255), 4)
        arcade.draw_text("ВАШ\nХОД", cx, cy, arcade.color.WHITE, 22 * s, font_name=FONT, align="center", anchor_x="center", anchor_y="center", multiline=True, width=int(radius * 2))
        fill, border, label, lc = (60, 40, 20), (200, 150, 50), "ЗАВЕРШИТЬ", arcade.color.WHITE
    else:
        arcade.draw_circle_filled(cx, cy, radius, (50, 50, 50, 150)); arcade.draw_circle_outline(cx, cy, radius, (100, 100, 100), 4)
        text = "ХОД\nВРАГА" if view.phase == "enemy" else "БОЙ!" if view.phase == "fight" else ""
        arcade.draw_text(text, cx, cy, arcade.color.LIGHT_GRAY, 18 * s, font_name=FONT, align="center", anchor_x="center", anchor_y="center", multiline=True, width=int(radius * 2))
        fill, border, label, lc = (30, 30, 30), (80, 80, 80), "ОЖИДАНИЕ", arcade.color.GRAY
    arcade.draw_lbwh_rectangle_filled(L.btn_x, L.btn_y, L.btn_w, L.btn_h, fill)
    arcade.draw_lbwh_rectangle_outline(L.btn_x, L.btn_y, L.btn_w, L.btn_h, border, 2)
    arcade.draw_text(label, cx, L.btn_y + L.btn_h / 2, lc, 14 * s, font_name=FONT, anchor_x="center", anchor_y="center")

    arcade.draw_lbwh_rectangle_filled(L.disc_x, L.disc_y, L.disc_w, L.disc_h, (30, 10, 10, 200))
    arcade.draw_lbwh_rectangle_outline(L.disc_x, L.disc_y, L.disc_w, L.disc_h, (120, 50, 50), 2)
    for i in range(min(len(view.discard_pile), 7)):
        arcade.draw_lbwh_rectangle_filled(L.disc_x + i*2*s, L.disc_y + i*2*s, L.disc_w, L.disc_h, (60, 30, 30, 150))
    arcade.draw_text("СБРОС", L.disc_x + L.disc_w / 2, L.disc_y + L.disc_h + 10 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name=FONT, anchor_x="center")
    arcade.draw_text(str(len(view.discard_pile)), L.disc_x + L.disc_w / 2, L.disc_y + L.disc_h / 2, arcade.color.WHITE, 26 * s, font_name=FONT, anchor_x="center", anchor_y="center")

    card = view.player.active
    if view.phase == "player" and card and card in view.player.hand:
        pulse = 0.5 + 0.5 * math.sin(view.time * 5)
        rgb = (120, 255, 140) if view.player.energy >= view.cards_by_id.get(card.texture_name, {}).get("cost", 1) else (255, 90, 90)
        ww, hh = SLOT_W * s, SLOT_H * s
        for slot in view.slot_sprite_list:
            if slot.grid_y == 1 and slot.card is None:
                left, bottom = slot.center_x - ww / 2, slot.center_y - hh / 2
                arcade.draw_lbwh_rectangle_filled(left, bottom, ww, hh, (*rgb, int(18 + 22 * pulse)))
                arcade.draw_lbwh_rectangle_outline(left, bottom, ww, hh, (*rgb, int(110 + 120 * pulse)), 3)

    if view._targeting_util and view.pending_util:
        target_type = view.UTIL_TARGETS.get(view.pending_util["id"])
        pulse = 0.5 + 0.5 * math.sin(view.time * 6)
        for c in view.card_sprite_list:
            if (target_type == "enemy_card" and c.player == view.enemy and not c.stealth) or (target_type == "ally_card" and c.player == view.player):
                arcade.draw_lbwh_rectangle_outline(c.center_x - c.width/2, c.center_y - c.height/2, c.width, c.height, (255, 200, 80, int(120 + 120 * pulse)), 4)

    base = h - L.top_h
    arcade.draw_lbwh_rectangle_filled(0, base, w, L.top_h, (0, 0, 0))
    arcade.draw_lbwh_rectangle_filled(0, base, w, 2, (90, 90, 100))
    icon_x, bar_y = 30 * s, base + 50 * s
    bar_x, bar_w = icon_x + 32 * s, 250 * s
    title = "БОСС" if view.is_boss else "ВРАГ — ОБУЧЕНИЕ" if view.is_tutorial else f"ВРАГ — НОЧЬ {view.night}"
    arcade.draw_text(title, icon_x, bar_y + 60 * s, arcade.color.WHITE, 22 * s, font_name=FONT, width=int(280 * s), anchor_y="baseline")
    if view.icon_hp: arcade.draw_texture_rect(view.icon_hp, arcade.LBWH(icon_x, bar_y + 29 * s, 27 * s, 27 * s))
    if view.icon_energy: arcade.draw_texture_rect(view.icon_energy, arcade.LBWH(icon_x, bar_y - 6 * s, 27 * s, 27 * s))
    
    def draw_bar(x, y, width, height, cur, max_val, col):
        arcade.draw_lbwh_rectangle_filled(x, y, width, height, (30, 30, 35))
        if cur > 0 and max_val > 0: arcade.draw_lbwh_rectangle_filled(x, y, width * (max(0, cur) / max_val), height, col)
        arcade.draw_lbwh_rectangle_outline(x, y, width, height, (100, 100, 100), 2)

    draw_bar(bar_x, bar_y + 30 * s, bar_w, 25 * s, view.enemy.hp, view.enemy.max_hp, arcade.color.RED)
    arcade.draw_text(f"HP: {view.enemy.hp}/{view.enemy.max_hp}", bar_x + 10 * s, bar_y + 35 * s, arcade.color.WHITE, 16 * s, font_name=FONT)
    draw_bar(bar_x, bar_y - 5 * s, bar_w, 25 * s, view.enemy.energy, view.enemy.max_energy, arcade.color.CYAN)
    arcade.draw_text(f"EN: {view.enemy.energy}/{view.enemy.max_energy}", bar_x + 10 * s, bar_y, arcade.color.WHITE, 16 * s, font_name=FONT)

    stats_right, hand_left = bar_x + bar_w, L.e_hand_x0
    area_x0, area_x1 = stats_right + 30 * s, hand_left - 30 * s
    area_w, area_h = max(0.0, area_x1 - area_x0), L.top_h - 12 * s
    hurt = view.vfx.hero["enemy"] / 0.45
    jx = random.uniform(-1, 1) * 9 * s * hurt
    if view.enemy_portrait and area_w > 10 * s:
        ratio = view.enemy_portrait.width / view.enemy_portrait.height
        p_h = area_h if area_w / area_h > ratio else area_w / ratio
        p_w = p_h * ratio if area_w / area_h > ratio else area_w
        p_x, p_y = area_x0 + (area_w - p_w) / 2 + jx, base + (L.top_h - p_h) / 2
        arcade.draw_texture_rect(view.enemy_portrait, arcade.LBWH(p_x, p_y, p_w, p_h))
        if hurt > 0: arcade.draw_lbwh_rectangle_filled(p_x, p_y, p_w, p_h, (255, 0, 0, int(150 * hurt)))
        arcade.draw_lbwh_rectangle_outline(p_x, p_y, p_w, p_h, (255, 255, 255, 255), 4)
    
    step = (L.e_hand_x1 - L.e_hand_x0) / 6
    ch, cw, cy = 150 * s, 150 * s * (768 / 1152), base + L.top_h / 2
    for i in range(6):
        cx = L.e_hand_x0 + step * (i + 0.5)
        if view.card_back: arcade.draw_texture_rect(view.card_back, arcade.LBWH(cx - cw / 2, cy - ch / 2, cw, ch))
        else:
            arcade.draw_lbwh_rectangle_filled(cx - cw / 2, cy - ch / 2, cw, ch, (40, 20, 20))
            arcade.draw_lbwh_rectangle_outline(cx - cw / 2, cy - ch / 2, cw, ch, (100, 50, 50), 2)

    arcade.draw_lbwh_rectangle_filled(0, 0, w, L.bot_h, (0, 0, 0))
    arcade.draw_lbwh_rectangle_filled(0, L.bot_h, w, 2, (90, 90, 100))
    arcade.draw_line(L.sep1, 0, L.sep1, L.bot_h, (90, 90, 100), 2)
    arcade.draw_line(L.sep2, 0, L.sep2, L.bot_h, (90, 90, 100), 2)

    avatar_size = 130 * s
    avatar_x, avatar_y = 20 * s, 35 * s
    frame_color = arcade.color.WHITE if view.player.hp / view.player.max_hp > 0.6 else arcade.color.YELLOW_ORANGE if view.player.hp / view.player.max_hp > 0.3 else arcade.color.DARK_RED
    hurt = view.vfx.hero["player"] / 0.45
    ax = avatar_x + random.uniform(-1, 1) * 8 * s * hurt
    arcade.draw_lbwh_rectangle_filled(ax, avatar_y, avatar_size, avatar_size, (10, 10, 14))
    if view.player_portrait:
        ratio = view.player_portrait.width / view.player_portrait.height
        p_h = avatar_size if avatar_size / avatar_size > ratio else avatar_size / ratio
        p_w = p_h * ratio if avatar_size / avatar_size > ratio else avatar_size
        arcade.draw_texture_rect(view.player_portrait, arcade.LBWH(ax + (avatar_size - p_w)/2, avatar_y + (avatar_size - p_h)/2, p_w, p_h))
    else: arcade.draw_text(view.player_name[0].upper(), ax + avatar_size/2, avatar_y + avatar_size/2, (90, 90, 100), 64 * s, font_name=FONT, anchor_x="center", anchor_y="center")
    if hurt > 0: arcade.draw_lbwh_rectangle_filled(ax, avatar_y, avatar_size, avatar_size, (255, 0, 0, int(150 * hurt)))
    arcade.draw_lbwh_rectangle_outline(ax, avatar_y, avatar_size, avatar_size, frame_color, 4)
    arcade.draw_text(f"УР.{view.player.level}", avatar_x, avatar_y + avatar_size + 5 * s, frame_color, 16 * s, font_name=FONT)

    icon_x = avatar_x + avatar_size + 15 * s
    bar_x, bar_w = icon_x + 32 * s, 190 * s
    if view.icon_hp: arcade.draw_texture_rect(view.icon_hp, arcade.LBWH(icon_x, avatar_y + 84 * s, 27 * s, 27 * s))
    if view.icon_energy: arcade.draw_texture_rect(view.icon_energy, arcade.LBWH(icon_x, avatar_y + 44 * s, 27 * s, 27 * s))
    draw_bar(bar_x, avatar_y + 85 * s, bar_w, 25 * s, view.player.hp, view.player.max_hp, arcade.color.RED)
    arcade.draw_text(f"HP: {view.player.hp}/{view.player.max_hp}", bar_x + 10 * s, avatar_y + 90 * s, arcade.color.WHITE, 14 * s, font_name=FONT)
    draw_bar(bar_x, avatar_y + 45 * s, bar_w, 25 * s, view.player.energy, view.player.max_energy, arcade.color.CYAN)
    arcade.draw_text(f"EN: {view.player.energy}/{view.player.max_energy}", bar_x + 10 * s, avatar_y + 50 * s, arcade.color.WHITE, 14 * s, font_name=FONT)
    draw_bar(bar_x, avatar_y + 5 * s, bar_w, 25 * s, view.profile.xp, view.profile.xp_to_next(), arcade.color.GOLD)
    arcade.draw_text(f"XP: {view.profile.xp}/{view.profile.xp_to_next()}", bar_x + 10 * s, avatar_y + 10 * s, arcade.color.WHITE, 14 * s, font_name=FONT)

    util_w, util_h, util_y = 90 * s, 120 * s, 45 * s
    arcade.draw_text("УТИЛИТЫ", L.util_x, L.bot_h - 25 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name=FONT)
    view._util_rects = []
    for i in range(3):
        ux = L.util_x + i * (util_w + 10 * s)
        view._util_rects.append((ux, util_y, util_w, util_h))
        util = view.player_utilities[i] if i < len(view.player_utilities) else None
        if util is None:
            arcade.draw_lbwh_rectangle_filled(ux, util_y, util_w, util_h, (10, 10, 14))
            arcade.draw_lbwh_rectangle_outline(ux, util_y, util_w, util_h, (50, 50, 60), 2)
            continue
        affordable = view.player.energy >= util.get("cost", 0)
        bg = (35, 30, 15) if affordable else (15, 15, 18)
        border = (255, 120, 60) if view.pending_util is util else (220, 180, 60) if affordable else (70, 70, 80)
        arcade.draw_lbwh_rectangle_filled(ux, util_y, util_w, util_h, bg)
        arcade.draw_lbwh_rectangle_outline(ux, util_y, util_w, util_h, border, 2)
        arcade.draw_text(util["name"], ux + 5 * s, util_y + util_h - 15 * s, arcade.color.WHITE if affordable else arcade.color.GRAY, 11 * s, font_name=FONT, width=int(util_w - 10 * s), align="center")
        arcade.draw_text(f"{util.get('cost', 0)}", ux + util_w - 8 * s, util_y + 5 * s, arcade.color.CYAN, 14 * s, font_name=FONT, anchor_x="right", anchor_y="bottom")

    abx, aby, abw, abh = avatar_x, 5 * s, avatar_size, 28 * s
    view._ability_btn_rect = (abx, aby, abw, abh)
    ready = view.phase == "player" and not view.player.ability_used and bool(view.player.ability_name)
    arcade.draw_lbwh_rectangle_filled(abx, aby, abw, abh, (35, 45, 35) if ready else (15, 15, 18))
    arcade.draw_lbwh_rectangle_outline(abx, aby, abw, abh, (100, 255, 120) if ready else (80, 80, 80), 2)
    arcade.draw_text(view.player.ability_name or "СПОСОБНОСТЬ", abx + abw / 2, aby + abh / 2, (100, 255, 120) if ready else (80, 80, 80), 11 * s, font_name=FONT, anchor_x="center", anchor_y="center", width=int(abw - 8 * s), align="center")
    
    arcade.draw_text("РУКА", L.hand_x0, L.bot_h - 25 * s, arcade.color.LIGHT_GRAY, 16 * s, font_name=FONT)
    step = (L.hand_x1 - L.hand_x0) / 6
    card_w, card_h = CARD_W * s, CARD_H * s
    start_x, cy = L.hand_x0 + step / 2, 88 * s
    for i in range(6):
        cx = start_x + i * step
        arcade.draw_lbwh_rectangle_filled(cx - card_w/2, cy - card_h/2, card_w, card_h, (5, 5, 8, 130))
        arcade.draw_lbwh_rectangle_outline(cx - card_w/2, cy - card_h/2, card_w, card_h, (40, 40, 48), 2)
    for i, card in enumerate(view.player.hand):
        target_scale = s * 1.1 if card.is_selected else s
        if getattr(card, "_applied_scale", None) != target_scale: card.scale = target_scale; card._applied_scale = target_scale
        card.center_x, card.center_y, card.alpha = start_x + i * step, cy, 255
    view.hand_sprite_list.draw(filter=gl.NEAREST)
    for card in view.player.hand: card.draw_highlight()

    x, y, pw, ph = L.panel_x, L.panel_y, L.panel_w, L.panel_h
    card = view.player.active or view._hovered_card
    util = None
    if not card and view._hovered_util_idx is not None and view._hovered_util_idx < len(view.player_utilities): util = view.player_utilities[view._hovered_util_idx]
    arcade.draw_lbwh_rectangle_filled(x, y, pw, ph, (15, 15, 20, 240))
    arcade.draw_lbwh_rectangle_outline(x, y, pw, ph, (100, 100, 100), 2)
    if util:
        arcade.draw_text(util["name"], x + 15 * s, y + ph - 40 * s, arcade.color.WHITE, 22 * s, font_name=FONT, width=int(pw - 30 * s))
        arcade.draw_text(f"Стоимость: {util.get('cost', 0)}", x + 15 * s, y + ph - 68 * s, arcade.color.CYAN, 14 * s, font_name=FONT)
        mech, _, lore = util.get("text", "").partition("\n\n")
        mech_t = arcade.Text(mech, x + 15 * s, y + ph - 100 * s, (235, 235, 235), 15 * s, width=int(pw - 30 * s), font_name=FONT, multiline=True, anchor_y="top")
        mech_t.draw()
        if lore: arcade.Text(lore, x + 15 * s, y + ph - 100 * s - mech_t.content_height - 14 * s, (140, 140, 150), 15 * s, width=int(pw - 30 * s), font_name=FONT, multiline=True, anchor_y="top").draw()
    elif card:
        info = view.cards_by_id.get(card.texture_name, {})
        rarity_name, rarity_color = view.RARITY.get(info.get("rarity"), ("", (170, 170, 170)))
        mine = card.player == view.player
        arcade.draw_text(info.get("name", card.texture_name), x + 15 * s, y + ph - 40 * s, arcade.color.WHITE, 22 * s, font_name=FONT, width=int(pw - 30 * s))
        arcade.draw_text(rarity_name, x + 15 * s, y + ph - 68 * s, rarity_color, 14 * s, font_name=FONT)
        arcade.draw_text("ваша карта" if mine else "карта врага", x + pw - 15 * s, y + ph - 68 * s, (120, 200, 120) if mine else (220, 100, 100), 14 * s, font_name=FONT, anchor_x="right")
        if view.icon_hp: arcade.draw_texture_rect(view.icon_hp, arcade.LBWH(x + 15 * s, y + ph - 128 * s, 30 * s, 30 * s))
        arcade.draw_text(f"{card.hp}", x + 52 * s, y + ph - 124 * s, arcade.color.RED, 22 * s, font_name=FONT)
        if view.icon_dmg: arcade.draw_texture_rect(view.icon_dmg, arcade.LBWH(x + 100 * s, y + ph - 128 * s, 30 * s, 30 * s))
        arcade.draw_text(f"{card.strength}", x + 137 * s, y + ph - 124 * s, arcade.color.GOLD, 22 * s, font_name=FONT)
        if "cost" in info:
            if view.icon_energy: arcade.draw_texture_rect(view.icon_energy, arcade.LBWH(x + 185 * s, y + ph - 128 * s, 30 * s, 30 * s))
            arcade.draw_text(f"{info['cost']}", x + 222 * s, y + ph - 124 * s, arcade.color.CYAN, 22 * s, font_name=FONT)
        desc_top = y + ph - 150 * s
        icon_kw = [k for k in info.get("keywords", []) if view.KEYWORD_ICON.get(k) in view.status_icons and view.status_icons[view.KEYWORD_ICON[k]]]
        if icon_kw:
            icon_h, icon_y, cx = 40 * s, y + ph - 190 * s, x + 20 * s
            for k in icon_kw:
                tex = view.status_icons[view.KEYWORD_ICON[k]]
                iw = icon_h * (tex.width / tex.height)
                arcade.draw_texture_rect(tex, arcade.LBWH(cx, icon_y, iw, icon_h))
                arcade.draw_text(view.KEYWORD_NAME[k], cx + iw + 6 * s, icon_y + icon_h / 2, arcade.color.WHITE, 15 * s, font_name=FONT, anchor_y="center")
                cx += iw + 6 * s + len(view.KEYWORD_NAME[k]) * 10 * s + 18 * s
            desc_top = icon_y - 16 * s
        full = info.get("text", card.description) or ""
        mech, _, lore = full.partition("\n\n")
        mech_t = arcade.Text(mech, x + 15 * s, desc_top, (235, 235, 235), 15 * s, width=int(pw - 30 * s), font_name=FONT, multiline=True, anchor_y="top")
        mech_t.draw()
        if lore: arcade.Text(lore, x + 15 * s, desc_top - mech_t.content_height - 14 * s, (140, 140, 150), 15 * s, width=int(pw - 30 * s), font_name=FONT, multiline=True, anchor_y="top").draw()
    else:
        arcade.draw_text("Выберите\nкарту", x + pw / 2, y + ph / 2, (110, 110, 120), 20 * s, font_name=FONT, width=int(pw - 30 * s), align="center", anchor_x="center", anchor_y="center", multiline=True)

    if view.dialog_text and view.dialog_age <= view.dialog_dur:
        x, w, h, y = 20 * s, w - 40 * s, L.dialog_h, L.dialog_y
        alpha = 220
        if view.dialog_age < 0.3: alpha = int(220 * (view.dialog_age / 0.3))
        elif view.dialog_age > view.dialog_dur - 0.4: alpha = int(220 * (1 - (view.dialog_age - (view.dialog_dur - 0.4)) / 0.4))
        alpha = max(0, min(220, alpha))
        arcade.draw_lbwh_rectangle_filled(x, y, w, h, (0, 0, 0, alpha))
        arcade.draw_lbwh_rectangle_outline(x, y, w, h, (255, 255, 255, 255), 3)
        key = (view.dialog_text, int(w), int(h))
        if view._dialog_cache_key != key:
            font_size = int(22 * s); txt = None
            while font_size >= 10:
                txt = arcade.Text(view.dialog_text, 0, 0, (240, 240, 240, 255), font_size, font_name=FONT, width=int(w - 30 * s), multiline=True, align="center")
                if txt.content_height <= h - 14 * s: break
                font_size -= 1
            view._dialog_cache, view._dialog_cache_key = txt, key
        if view._dialog_cache:
            view._dialog_cache.color = (240, 240, 240, min(255, alpha + 30))
            view._dialog_cache.x, view._dialog_cache.y = x + w / 2, y + h / 2 + view._dialog_cache.content_height / 2
            view._dialog_cache.anchor_x, view._dialog_cache.anchor_y = "center", "top"
            view._dialog_cache.draw()

    if view._targeting_util: arcade.draw_text("ВЫБЕРИТЕ ЦЕЛЬ (ПКМ — отмена)", L.w / 2, L.mid, (255, 200, 80), 26 * L.s, font_name=FONT, anchor_x="center", anchor_y="center")