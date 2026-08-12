import asyncio
import random

from bot.game.entities.items import Items

async def buy_item(item_arr, amount_items):
    items = Items()

    unique_items = list(set(item_arr))
    multiple_items = len(unique_items) > 1

    for i, item_id in enumerate(unique_items):
        for _ in range(amount_items):
            await items.find_and_buy_item(item_id)
            await asyncio.sleep(random.uniform(0.54, 0.76))

        if multiple_items and i > 0 and i % 4 == 0 and i != (len(unique_items) - 1):
            await items.finalize_basket()
            await asyncio.sleep(random.uniform(0.71, 0.93))

    await items.finalize_basket()
    await asyncio.sleep(random.uniform(0.61, 0.88))
    await items.close_shop()