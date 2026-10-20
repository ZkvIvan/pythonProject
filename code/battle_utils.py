import random

def use_utility(view, uid, target):
    t = target
    if uid == "util_01": view.player.heal(5)
    elif uid == "util_02" and t: view.damage_card(t, 3)
    elif uid == "util_03" and t: t.keywords.append("shield") if "shield" not in t.keywords else None
    elif uid == "util_04": view.player.energy += 1; view.player.hp = max(0, view.player.hp - 3)
    elif uid == "util_05":
        for c in list(view.enemy.cards): view.damage_card(c, 1)
    elif uid == "util_06" and t: t.strength += 2; view.player.hp = max(0, view.player.hp - 2)
    elif uid == "util_07" and t: t.frozen_turns = 1
    elif uid == "util_08" and t: view.damage_card(t, 4)
    elif uid == "util_09" and t and t.player == view.player: view.damage_card(t, 999); view.enemy.take_damage(5)
    elif uid == "util_10":
        if cid := view.player.draw_card_id(): view._spawn_player_card(cid)
    elif uid == "util_11":
        for _ in range(2):
            if cid := view.player.draw_card_id(): view._spawn_player_card(cid)
        view.player.hp = max(0, view.player.hp - 5)
    elif uid == "util_12" and t: t.strength = max(0, t.strength - 2)
    elif uid == "util_13" and t: t.strength += 3
    elif uid == "util_14":
        for c in view.player.cards: c.hp = min(c.max_hp, c.hp + 3)
    elif uid == "util_15":
        for c in list(view.card_sprite_list): view.damage_card(c, 2)
    elif uid == "util_16" and t: view.damage_card(t, 2); view.player.heal(2)
    elif uid == "util_17" and t: view.damage_card(t, 6)
    elif uid == "util_18" and t: t.keywords = [k for k in t.keywords if k == "flying"]
    else: return False
    return True