import asyncio
import random

from bot.core.driver import MyDriver
from bot.game.entities.items import Items

async def craft_recipe():
    items = Items()
    await items.open_crafting()
    await asyncio.sleep(random.uniform(1.21, 1.42))
    recipe = await items.fetch_recipes()
    if not recipe:
        return

    recipe_id = recipe["id"]
    await items.select_recipe(recipe_id)
    await asyncio.sleep(random.uniform(0.61, 0.88))
    await items.confirm_selected_recipe(recipe_id)
    await asyncio.sleep(random.uniform(0.56, 0.65))
    await items.accept_recipe()
    await asyncio.sleep(random.uniform(0.52, 0.63))
    await items.close_crafting()
    await asyncio.sleep(random.uniform(0.5, 0.66))

async def craft_item():
    items = Items()
    barter_data = await items.fetch_barter_data()
    if not barter_data:
        return

    offer_id = barter_data["offerId"]
    item_id = barter_data["itemId"]
    category = barter_data["category"]
    print(
        f"⚙️ Creating item: offer_id={offer_id}, item_id={item_id}, category={category}"
    )
    await items.find_barter_offer(offer_id)
    await asyncio.sleep(random.uniform(0.71, 0.98))
    await items.do_barter(item_id)
    await asyncio.sleep(random.uniform(0.76, 0.96))
    await items.finish_barter()
    await asyncio.sleep(random.uniform(0.61, 0.88))


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