import asyncio
import random

from bot.game.entities.items import Items
from bot.game.entities.player import Player
from bot.game.entities.player_interactions import PlayerInteractions
from bot.game.services.map_services import current_location_map
from bot.game.services.move_service import a_star


async def collect_item(goal):
    items = Items()
    actions = PlayerInteractions()
    player = Player()

    current_location = await current_location_map()
    start_position = await player.position()
    start = (start_position[0], start_position[1])
    checker = start
    path = a_star(current_location, start, goal)
    for i in path:
        resultX, resultY = i
        if i == path[-1]:
            await actions.move_hero(resultX, resultY)
    while checker != path[-1]:
        start_position = await player.position()
        checker = (start_position[0], start_position[1])
        await asyncio.sleep(random.uniform(0.12, 0.25))
    await items.locate_and_collect_item()
    await asyncio.sleep(random.uniform(0.47, 0.64))
