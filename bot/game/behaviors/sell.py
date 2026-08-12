import asyncio
import math
import random

from bot.game.entities.items import Items


async def sell_items():
    items = Items()
    bag_data = await items.get_bags_with_items_data()

    if not bag_data:
        return

    for _ in range(20):
        if await items.is_shop_open():
            break
        await asyncio.sleep(0.2)
    else:
        print("⚠️ sell_items: sklep się nie otworzył, pomijam sprzedaż")
        return

    for bag in bag_data:
        index = bag["index"]
        items_in_bag = bag["actual_items_amount"]

        batches = min(math.ceil(items_in_bag / 20), 2)
        await asyncio.sleep(random.uniform(0.25, 0.35))
        for _ in range(batches):
            await items.quick_sell_items(index + 1)
            await asyncio.sleep(random.uniform(0.85, 1.15))
            await items.finalize_basket()
            await asyncio.sleep(random.uniform(0.61, 0.85))
        await asyncio.sleep(random.uniform(0.61, 0.85))
    await items.close_shop()
