import asyncio
import random

from bot.game.entities.items import Items


async def equip_item(item_arr):
    items = Items()
    if not item_arr:
        return
    for item_id in item_arr:
        await items.equip_item(item_id)
        await asyncio.sleep(random.uniform(0.64, 0.91))