import asyncio
import math
import random
from bot.core.driver import MyDriver
from bot.game.moving.pathfiding import a_star
from bot.utils.helpers import (
    current_location_map,
    current_position,
)


async def equip_item(item_arr):
    driver = await MyDriver().get_driver()
    if not item_arr:
        return
    for item_id in item_arr:
        script = f"""() => _g("moveitem&st=1&id={item_id}")"""
        await driver.evaluate(script, isolated_context=False)
        await asyncio.sleep(random.uniform(0.64, 0.91))


async def buy_item(item_arr, amount_items):
    driver = await MyDriver().get_driver()

    unique_items = list(set(item_arr))
    multiple_items = len(unique_items) > 1

    for i, item_id in enumerate(unique_items):
        for _ in range(amount_items):
            script = f"""
                (() => {{
                    let item = Object.values(window.Engine.shop.items).find(i => i.id == '{item_id}');
                    if(item) {{
                        window.Engine.shop.basket.buyItem(item);
                    }}
                }})()
            """
            await driver.evaluate(script, isolated_context=False)
            await asyncio.sleep(random.uniform(0.54, 0.76))

        if multiple_items and i > 0 and i % 4 == 0 and i != (len(unique_items) - 1):
            await driver.evaluate(
                "window.Engine.shop.basket.finalize()", isolated_context=False
            )
            await asyncio.sleep(random.uniform(0.71, 0.93))

    await driver.evaluate(
        "window.Engine.shop.basket.finalize()", isolated_context=False
    )
    await asyncio.sleep(random.uniform(0.61, 0.88))
    await driver.evaluate("window.Engine.shop.close()", isolated_context=False)


async def get_items_amount():
    driver = await MyDriver().get_driver()
    script = """
        () => {
            return window.Engine.heroEquipment.getFreeSlots();
        }
    """
    items_amount = await driver.evaluate(script, isolated_context=False)
    return items_amount


async def get_bags_with_items():
    driver = await MyDriver().get_driver()
    script = """
        () => {
            const validBags = window.Engine.bags
                .filter(b => b && Array.isArray(b) && b[2] !== 1195874772);

            const result = validBags
                .map(([max_size, actual_items_amount, location], index) => ({
                    index,
                    max_size,
                    actual_items_amount,
                    location
                }))
                .filter(b => b.actual_items_amount > 1);

            return result;
        }
    """
    bag_data = await driver.evaluate(script, isolated_context=False)
    return bag_data


async def quick_sell_items():
    driver = await MyDriver().get_driver()
    bag_data = await get_bags_with_items()

    if not bag_data:
        return

    for bag in bag_data:
        index = bag["index"]
        items = bag["actual_items_amount"]

        batches = min(math.ceil(items / 20), 2)

        for _ in range(batches):
            script = f"() => window.Engine.shop.greatMerchant({index})"
            await driver.evaluate(script, isolated_context=False)
            await asyncio.sleep(random.uniform(0.55, 0.75))
            script = f"""
                () => window.Engine.shop.basket.finalize()
            """
            await driver.evaluate(script, isolated_context=False)
            await asyncio.sleep(random.uniform(0.61, 0.85))
    script = f"""
        () => window.Engine.shop.close()
    """
    await driver.evaluate(script, isolated_context=False)


async def filter_items_for_sale():
    driver = await MyDriver().get_driver()
    script = """
        () => {
            items = window.Engine.items
                .fetchLocationItems("g")
                .filter((item) =>
                    item._cachedStats.hasOwnProperty("rarity") &&
                    item._cachedStats.rarity === "common",
                )
                .filter((item) =>
                    (!item._cachedStats.hasOwnProperty("leczy") ||
                    item._cachedStats.leczy < 500) &&
                    (!item._cachedStats.hasOwnProperty("teleport") ||
                    item._cachedStats.teleport === ""),
                )
                .filter((item) =>
                    item._cachedStats.hasOwnProperty("lvl") &&
                    parseInt(item._cachedStats.lvl, 4) < 30,
                )
                .filter((item) =>
                    !item._cachedStats.hasOwnProperty("bag") ||
                    parseInt(item._cachedStats.bag, 4) < 1,
                );

            let x = items;
            eqItems = window.Engine.heroEquipment.getEqItems();
            let y = Object.values(eqItems);
            let filteredItems = x.filter((item) => !y.includes(item));
            return filteredItems
        }
    """
    filtered_items = await driver.evaluate(script, isolated_context=False)
    return filtered_items


async def sell_item():
    driver = await MyDriver().get_driver()
    itemArr = await filter_items_for_sale()
    amountItems = len(itemArr)
    for i in range(amountItems):
        item = itemArr[i]
        script = f"""
            () => window.Engine.shop.basket.sellItem({item})
        """
        await driver.evaluate(script, isolated_context=False)
        await asyncio.sleep(random.uniform(0.54, 0.76))
        if i > 0 and i % 19 == 0 and i != (amountItems - 1):
            script = f"""
                () => window.Engine.shop.basket.finalize()
            """
            await driver.evaluate(script, isolated_context=False)
            await asyncio.sleep(random.uniform(0.71, 0.93))
    script = f"""
        () => window.Engine.shop.basket.finalize()
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.61, 0.88))
    script = f"""
        () => window.Engine.shop.close()
    """
    await driver.evaluate(script, isolated_context=False)


async def collect_item(goal):
    driver = await MyDriver().get_driver()
    current_location = await current_location_map()
    start_position = await current_position()
    start = (start_position[0], start_position[1])
    checker = start
    path = a_star(current_location, start, goal)
    for i in path:
        resultX, resultY = i
        if i == path[-1]:
            script = f"""
                    () => window.Engine.hero.searchPath({{
                        x: {resultX},
                        y: {resultY}
                    }}, !1);
                """
            await driver.evaluate(script, isolated_context=False)
    while checker != path[-1]:
        start_position = await current_position()
        checker = (start_position[0], start_position[1])
        await asyncio.sleep(random.uniform(0.12, 0.25))
    script = """
        (function() {
            const {x: t, y: e} = Engine.hero.d, i = Engine.map.groundItems.getGroundItemOnPosition(t, e);
            i.length > 0 && _g("takeitem&id=" + i[0].id);
            const n = Engine.npcs.getRenewableNpcByPosition(t, e);
            n && Engine.hero.sendRequestToTalk(n.d.id)
        })();
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.47, 0.64))


async def open_and_create_recipe():
    driver = await MyDriver().get_driver()
    script = f"""
        () => window.Engine.crafting.triggerOpen()
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(1.21, 1.42))

    recipe = await driver.evaluate(
        """
        (() => {
            const recipes = window.Engine.crafting.recipes.recipes;
            if (!recipes) return null;
            const active = Object.entries(recipes)
                .find(([id, data]) => data.enabled === 1);
            if (!active) return null;
            const [id, data] = active;
            return { id: parseInt(id), name: data.name };
        })();
        """,
        isolated_context=False,
    )

    if not recipe:
        return

    recipe_id = recipe["id"]

    await driver.evaluate(
        f"() => window.Engine.crafting.recipes.showRecipe({recipe_id})",
        isolated_context=False,
    )
    await asyncio.sleep(random.uniform(0.61, 0.88))

    script = f"""
        () => window.Engine.crafting.recipes.showRecipe({recipe_id})
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.61, 0.86))

    script = f"""
        () => window.Engine.crafting.recipes.confirmUseRecipe({recipe_id})
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.56, 0.65))

    script = f"""
        () => window.Engine.hotKeys.checkCanAcceptAlert()
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.52, 0.63))

    script = f"""
        () => window.Engine.crafting.triggerClose()
    """
    await driver.evaluate(script, isolated_context=False)
    await asyncio.sleep(random.uniform(0.5, 0.66))


async def create_item():
    driver = await MyDriver().get_driver()

    barter_data = await driver.evaluate(
        """
        (() => {
            const categories = window.Engine?.barter?.allCategories;
            if (!categories) return null;
            for (const catKey in categories) {
                const catItems = categories[catKey];
                if (!Array.isArray(catItems)) continue;
                for (const item of catItems) {
                    if (item.maxAmount === 1) {
                        return {
                            offerId: item.affectedId,
                            itemId: item.id,
                            category: item.category
                        };
                    }
                }
            }
            return null;
        })();
        """,
        isolated_context=False,
    )

    if not barter_data:
        return

    offer_id = barter_data["offerId"]
    item_id = barter_data["itemId"]
    category = barter_data["category"]
    print(
        f"⚙️ Creating item: offer_id={offer_id}, item_id={item_id}, category={category}"
    )

    find_offer = f"""
        () => {{
            const offerList = window.Engine.barter.createOneOfferOnList(window.Engine.barter.allParseOffers[{offer_id}]);
            if (offerList && offerList[0]) {{
                window.Engine.barter.recipeClick(offerList[0], offerList[0]);
            }}
        }}
    """
    await driver.evaluate(find_offer, isolated_context=False)
    await asyncio.sleep(random.uniform(0.71, 0.98))

    craft_item = f"() => window.Engine.barter.doBarter({item_id})"
    await driver.evaluate(craft_item, isolated_context=False)
    await asyncio.sleep(random.uniform(0.76, 0.96))

    close_barter = "() => window.Engine.barter.close()"
    await driver.evaluate(close_barter, isolated_context=False)
    await asyncio.sleep(random.uniform(0.61, 0.88))


async def get_item_id_by_name(item_name):
    driver = await MyDriver().get_driver()
    script = f"""
    () => {{
        item = window.Engine.items.fetchLocationItems("g").filter(item => item.name === '{item_name}');
        let id = item.map(x => x.id);
        return id;
    }}
    """
    item_id = await driver.evaluate(script, isolated_context=False)
    return item_id
