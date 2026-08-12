import asyncio
from bot.game.entities.items import Items
from bot.game.entities.player import Player
from bot.game.entities.player_inventory import PlayerInventory


async def heal_hero(heal_event):
    player = Player()
    player_eq = PlayerInventory()
    items = Items()
    hp_info_list = await player.hp_stats()
    max_hp, hp, hp_stat = hp_info_list
    if hp is not None and hp < 0.8 * max_hp:
        hp_stat = hp
        while hp_stat < 0.92 * max_hp:
            potions = await player_eq.get_potions()
            if not potions:
                    return

            potion_id = potions[-1]
            await items.use_potion(potion_id)

            await asyncio.sleep(0.2)
            hp_info_list = await player.hp_stats()
            hp_stat = hp_info_list[2]
    heal_event.clear()
