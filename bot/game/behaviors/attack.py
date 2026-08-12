import asyncio
import random
from bot.game.entities.mob import Mob
from bot.game.entities.player import Player
from bot.game.entities.player_interactions import PlayerInteractions
from bot.integrations.dsc_loot_notifier import dsc_loot_msg, heroes_dsc_loot_msg


async def attack_mob(mob: Mob, heroes: bool = False, heal_event: asyncio.Event | None = None) -> None:
    actions = PlayerInteractions()
    player = Player()

    while await mob.is_mob_alive():
        if await actions.is_fight_active():
            await actions.set_auto_fight()
            await asyncio.sleep(random.uniform(0.1, 0.2))
            continue
        await actions.request_hero_attack(mob.id)
        await asyncio.sleep(random.uniform(0.72, 1.09))

    if await player.is_dead():
        return

    if heal_event:
        heal_event.set()

    if heroes:
        await heroes_dsc_loot_msg(mob.name)
    else:
        await dsc_loot_msg(mob.name)